import base64
from dataclasses import dataclass
from math import atan2
from typing import Any

import cv2
import numpy as np


@dataclass(frozen=True)
class RoomDetectionParams:
    threshold_value: int = 200
    close_h_ksize: tuple[int, int] = (15, 3)
    close_v_ksize: tuple[int, int] = (3, 15)
    dilate_iterations: int = 2
    open_ksize: int = 5
    min_room_area_ratio: float = 0.001
    approx_eps_ratio: float = 0.02
    snap_tolerance: int = 5


def _order_clockwise(points_xy: np.ndarray) -> np.ndarray:
    pts = np.asarray(points_xy, dtype=np.float32)
    center = pts.mean(axis=0)
    angles = np.array([atan2(p[1] - center[1], p[0] - center[0]) for p in pts])
    order = np.argsort(angles)
    pts = pts[order][::-1]
    return pts.astype(np.int32)


def _snap_axis_aligned(pts: np.ndarray, tol: int = 5) -> np.ndarray:
    """Snap points to axis-aligned grid for clean rectangular rooms"""
    snapped = pts.copy()
    n = len(pts)
    
    # Snap x-coordinates
    for i in range(n):
        for j in range(n):
            if i != j and abs(pts[i][0] - pts[j][0]) < tol:
                snapped[i][0] = pts[j][0]
    
    # Snap y-coordinates
    for i in range(n):
        for j in range(n):
            if i != j and abs(pts[i][1] - pts[j][1]) < tol:
                snapped[i][1] = pts[j][1]
    
    return snapped


def _encode_png_data_url(image_bgr: np.ndarray) -> str:
    ok, buf = cv2.imencode(".png", image_bgr)
    if not ok:
        raise ValueError("Failed to encode overlay PNG")
    b64 = base64.b64encode(buf.tobytes()).decode("ascii")
    return f"data:image/png;base64,{b64}"


def detect_rooms_and_overlay(
    image_bgr: np.ndarray,
    scale_m_per_px: float,
    params: RoomDetectionParams | None = None,
) -> dict[str, Any]:
    if params is None:
        params = RoomDetectionParams()

    if scale_m_per_px <= 0:
        raise ValueError("scale_m_per_px must be > 0")

    # Step 1: Grayscale conversion
    gray = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2GRAY)
    
    # Calculate minimum room area based on image size
    total_area_px = gray.shape[0] * gray.shape[1]
    min_room_area_px = total_area_px * params.min_room_area_ratio
    
    # Step 2: Fixed threshold (Binary)
    _, walls = cv2.threshold(
        gray, params.threshold_value, 255, cv2.THRESH_BINARY_INV
    )
    
    # Step 3: Wall Closing (H + V kernels separately)
    kernel_h = cv2.getStructuringElement(cv2.MORPH_RECT, params.close_h_ksize)
    kernel_v = cv2.getStructuringElement(cv2.MORPH_RECT, params.close_v_ksize)
    
    walls = cv2.morphologyEx(walls, cv2.MORPH_CLOSE, kernel_h)
    walls = cv2.morphologyEx(walls, cv2.MORPH_CLOSE, kernel_v)
    
    # Step 4: Wall Thickening
    walls = cv2.dilate(walls, None, iterations=params.dilate_iterations)
    
    # Step 5: Remove small noise (Open operation)
    if params.open_ksize > 1:
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (params.open_ksize, params.open_ksize))
        walls = cv2.morphologyEx(walls, cv2.MORPH_OPEN, kernel)
    
    # Step 6: Flood Fill Exterior from all borders
    h, w = walls.shape
    mask = walls.copy()
    ff_mask = np.zeros((h + 2, w + 2), np.uint8)
    
    # Flood fill from top-left corner (exterior is always connected to borders)
    cv2.floodFill(mask, ff_mask, (0, 0), 255)
    
    # Step 7: Invert to get rooms
    rooms_mask = cv2.bitwise_not(mask)
    
    # Additional cleanup: remove remaining walls
    rooms_mask = cv2.bitwise_and(rooms_mask, cv2.bitwise_not(walls))
    
    # Step 8: Find contours
    contours, _ = cv2.findContours(rooms_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    rooms: list[dict[str, Any]] = []
    
    for cnt in contours:
        area_px = float(cv2.contourArea(cnt))
        if area_px < min_room_area_px:
            continue
        
        peri_px = float(cv2.arcLength(cnt, True))
        if peri_px == 0:
            continue
        
        # Step 9: Polygon simplification
        eps = params.approx_eps_ratio * peri_px
        approx = cv2.approxPolyDP(cnt, eps, True).reshape(-1, 2)
        
        if approx.shape[0] < 3:
            continue
        
        # Step 10: Axis-aligned polygon snapping
        approx = _snap_axis_aligned(approx, params.snap_tolerance)
        
        # Order clockwise
        approx = _order_clockwise(approx)
        
        points_px = [{"x": int(p[0]), "y": int(p[1])} for p in approx]
        
        # Calculate edge lengths
        edge_lengths_px: list[float] = []
        for i in range(len(approx)):
            p1 = approx[i]
            p2 = approx[(i + 1) % len(approx)]
            dx = float(p2[0] - p1[0])
            dy = float(p2[1] - p1[1])
            edge_lengths_px.append((dx * dx + dy * dy) ** 0.5)
        
        edge_lengths_m = [v * scale_m_per_px for v in edge_lengths_px]
        perimeter_m = sum(edge_lengths_m)
        area_m2 = area_px * (scale_m_per_px ** 2)
        
        rooms.append(
            {
                "id": len(rooms),
                "polygon_px": points_px,
                "edge_lengths_m": edge_lengths_m,
                "perimeter_m": perimeter_m,
                "area_m2": area_m2,
                "area_px": area_px,
                "num_corners": len(approx),
            }
        )
    
    # Create overlay
    overlay = image_bgr.copy()
    
    # Draw each room with different colors
    colors = [
        (0, 255, 0),    # Green
        (255, 0, 0),    # Blue
        (0, 0, 255),    # Red
        (255, 255, 0),  # Cyan
        (255, 0, 255),  # Magenta
        (0, 255, 255),  # Yellow
    ]
    
    for room in rooms:
        pts = np.array(
            [[p["x"], p["y"]] for p in room["polygon_px"]], dtype=np.int32
        ).reshape(-1, 1, 2)
        
        color = colors[room["id"] % len(colors)]
        cv2.polylines(overlay, [pts], True, color, 3)
        
        # Calculate centroid
        center = pts.reshape(-1, 2).mean(axis=0).astype(int)
        
        # Draw label with background
        label = f"R{room['id']}: {room['area_m2']:.1f}m² ({room['num_corners']} sides)"
        font = cv2.FONT_HERSHEY_SIMPLEX
        font_scale = 0.5
        thickness = 1
        
        (label_w, label_h), baseline = cv2.getTextSize(label, font, font_scale, thickness)
        
        # Draw background rectangle
        cv2.rectangle(
            overlay,
            (center[0] - label_w // 2 - 5, center[1] - label_h - 5),
            (center[0] + label_w // 2 + 5, center[1] + 5),
            (255, 255, 255),
            -1,
        )
        
        # Draw text
        cv2.putText(
            overlay,
            label,
            (center[0] - label_w // 2, center[1]),
            font,
            font_scale,
            (0, 0, 0),
            thickness,
        )
    
    # Add metadata
    cv2.putText(
        overlay,
        f"Scale: {scale_m_per_px:.6f} m/px | Rooms: {len(rooms)}",
        (10, 30),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.7,
        (255, 255, 255),
        2,
    )
    cv2.putText(
        overlay,
        f"Scale: {scale_m_per_px:.6f} m/px | Rooms: {len(rooms)}",
        (10, 30),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.7,
        (0, 0, 0),
        1,
    )
    
    return {
        "rooms": rooms,
        "overlay_png_data_url": _encode_png_data_url(overlay),
        "image_width_px": int(image_bgr.shape[1]),
        "image_height_px": int(image_bgr.shape[0]),
        "total_rooms": len(rooms),
        "debug_masks": {
            "walls": _encode_png_data_url(cv2.cvtColor(walls, cv2.COLOR_GRAY2BGR)),
            "rooms": _encode_png_data_url(cv2.cvtColor(rooms_mask, cv2.COLOR_GRAY2BGR)),
        },
    }