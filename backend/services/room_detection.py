import base64
from dataclasses import dataclass
from math import atan2, sqrt
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
    
    # Step 2: Binary threshold (Inverted)
    _, binary = cv2.threshold(gray, params.threshold_value, 255, cv2.THRESH_BINARY_INV)
    
    # --- Detection logic ---
    
    # 1. Walls (using morphological operations)
    kernel_h = cv2.getStructuringElement(cv2.MORPH_RECT, params.close_h_ksize)
    kernel_v = cv2.getStructuringElement(cv2.MORPH_RECT, params.close_v_ksize)
    walls_mask = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel_h)
    walls_mask = cv2.morphologyEx(walls_mask, cv2.MORPH_CLOSE, kernel_v)
    walls_mask = cv2.dilate(walls_mask, None, iterations=params.dilate_iterations)
    
    # 2. Rooms (Flood fill exterior)
    h, w = walls_mask.shape
    mask = walls_mask.copy()
    ff_mask = np.zeros((h + 2, w + 2), np.uint8)
    cv2.floodFill(mask, ff_mask, (0, 0), 255)
    rooms_mask = cv2.bitwise_not(mask)
    rooms_mask = cv2.bitwise_and(rooms_mask, cv2.bitwise_not(walls_mask))
    
    # 3. Doors (Advanced: Look for arcs or gaps)
    # Simple heuristic: Small gaps in walls or specific shapes
    # (For this example, we'll use a simpler 'gap' detection)
    doors = []
    
    # 4. Windows (Advanced: Look for double lines)
    windows = []
    
    # --- Process Rooms ---
    total_area_px = gray.shape[0] * gray.shape[1]
    min_room_area_px = total_area_px * params.min_room_area_ratio
    contours, _ = cv2.findContours(rooms_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    rooms: list[dict[str, Any]] = []
    for cnt in contours:
        area_px = float(cv2.contourArea(cnt))
        if area_px < min_room_area_px: continue
        
        peri_px = float(cv2.arcLength(cnt, True))
        if peri_px == 0: continue
        
        eps = params.approx_eps_ratio * peri_px
        approx = cv2.approxPolyDP(cnt, eps, True).reshape(-1, 2)
        if approx.shape[0] < 3: continue
        
        approx = _snap_axis_aligned(approx, params.snap_tolerance)
        approx = _order_clockwise(approx)
        
        points_px = [{"x": int(p[0]), "y": int(p[1])} for p in approx]
        area_m2 = area_px * (scale_m_per_px ** 2)
        
        rooms.append({
            "id": len(rooms),
            "polygon_px": points_px,
            "area_m2": area_m2,
            "num_corners": len(approx),
        })

    # --- Overlay Creation ---
    overlay = image_bgr.copy()
    
    # Draw Rooms
    for room in rooms:
        pts = np.array([[p["x"], p["y"]] for p in room["polygon_px"]], dtype=np.int32).reshape(-1, 1, 2)
        cv2.polylines(overlay, [pts], True, (0, 255, 0), 2)
        center = pts.reshape(-1, 2).mean(axis=0).astype(int)
        cv2.putText(overlay, f"RM {room['id']}", tuple(center), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 1)

    # Draw "Detected" Walls (overlaying the mask for visualization)
    # We can use Hough lines to actually "detect" them as entities
    lines = cv2.HoughLinesP(walls_mask, 1, np.pi/180, threshold=50, minLineLength=40, maxLineGap=10)
    if lines is not None:
        for line in lines:
            x1, y1, x2, y2 = line[0]
            cv2.line(overlay, (x1, y1), (x2, y2), (0, 0, 255), 2) # Red for walls

    return {
        "rooms": rooms,
        "overlay_png_data_url": _encode_png_data_url(overlay),
        "total_rooms": len(rooms),
        "elements": {
            "walls": len(lines) if lines is not None else 0,
            "doors": 0, # CV detection for doors/windows is hard without templates
            "windows": 0
        }
    }