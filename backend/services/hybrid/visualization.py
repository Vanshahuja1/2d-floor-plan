"""
Visualization Module
Purpose: Create annotated overlay images showing all detected elements
Tech: OpenCV drawing functions
"""
import cv2
import numpy as np
import base64
from typing import Any


def _encode_png_data_url(image_bgr: np.ndarray) -> str:
    """Encode image as base64 data URL"""
    ok, buf = cv2.imencode(".png", image_bgr)
    if not ok:
        raise ValueError("Failed to encode overlay PNG")
    b64 = base64.b64encode(buf.tobytes()).decode("ascii")
    return f"data:image/png;base64,{b64}"


def create_annotated_overlay(
    image_bgr: np.ndarray,
    rooms: list[dict],
    walls: list[dict],
    doors: list[dict],
    windows: list[dict],
    scale_m_per_px: float
) -> str:
    """
    Create a beautiful annotated overlay showing all detected elements.
    
    Args:
        image_bgr: Original floor plan image
        rooms: Room data (in pixels)
        walls: Wall data (in pixels)
        doors: Door data (in pixels)
        windows: Window data (in pixels)
        scale_m_per_px: Scale factor
        
    Returns:
        Base64 encoded PNG data URL
    """
    # Create overlay on original image
    overlay = image_bgr.copy()
    
    # Define colors (BGR format)
    ROOM_COLOR = (144, 238, 144)      # Light green
    WALL_COLOR = (0, 0, 255)          # Red
    DOOR_COLOR = (0, 165, 255)        # Orange
    WINDOW_COLOR = (255, 144, 30)     # Blue
    TEXT_BG_COLOR = (255, 255, 255)   # White
    TEXT_COLOR = (0, 0, 0)            # Black
    
    # 1. Draw Walls (first, as base layer)
    for i, wall in enumerate(walls):
        start = tuple(wall['start'])
        end = tuple(wall['end'])
        cv2.line(overlay, start, end, WALL_COLOR, 3)
        
        # Add wall label at midpoint
        mid_x = int((start[0] + end[0]) / 2)
        mid_y = int((start[1] + end[1]) / 2)
        
        length_m = wall['length'] * scale_m_per_px
        label = f"W{i}: {length_m:.2f}m"
        
        # Draw text with background
        font = cv2.FONT_HERSHEY_SIMPLEX
        font_scale = 0.4
        thickness = 1
        (w, h), _ = cv2.getTextSize(label, font, font_scale, thickness)
        
        cv2.rectangle(overlay, (mid_x - 2, mid_y - h - 2), (mid_x + w + 2, mid_y + 2), TEXT_BG_COLOR, -1)
        cv2.putText(overlay, label, (mid_x, mid_y), font, font_scale, WALL_COLOR, thickness)
    
    # 2. Draw Rooms (polygons)
    for room in rooms:
        # Convert polygon to numpy array
        pts = np.array([[p[0], p[1]] for p in room['polygon']], dtype=np.int32)
        pts = pts.reshape((-1, 1, 2))
        
        # Draw filled polygon with transparency
        temp = overlay.copy()
        cv2.fillPoly(temp, [pts], ROOM_COLOR)
        cv2.addWeighted(temp, 0.3, overlay, 0.7, 0, overlay)
        
        # Draw polygon outline
        cv2.polylines(overlay, [pts], True, ROOM_COLOR, 2)
        
        # Calculate centroid
        M = cv2.moments(pts)
        if M["m00"] != 0:
            cx = int(M["m10"] / M["m00"])
            cy = int(M["m01"] / M["m00"])
        else:
            cx, cy = pts[0][0]
        
        # Draw room label
        area_m2 = room['area_px'] * (scale_m_per_px ** 2)
        label = f"Room {room['id']}"
        sublabel = f"{area_m2:.1f}m²"
        
        font = cv2.FONT_HERSHEY_SIMPLEX
        font_scale = 0.6
        thickness = 2
        
        (w1, h1), _ = cv2.getTextSize(label, font, font_scale, thickness)
        (w2, h2), _ = cv2.getTextSize(sublabel, font, 0.4, 1)
        
        # Background rectangle
        cv2.rectangle(overlay, (cx - w1//2 - 5, cy - h1 - h2 - 5), 
                     (cx + max(w1, w2)//2 + 5, cy + 5), TEXT_BG_COLOR, -1)
        cv2.rectangle(overlay, (cx - w1//2 - 5, cy - h1 - h2 - 5), 
                     (cx + max(w1, w2)//2 + 5, cy + 5), ROOM_COLOR, 1)
        
        # Text
        cv2.putText(overlay, label, (cx - w1//2, cy - h2), font, font_scale, TEXT_COLOR, thickness)
        cv2.putText(overlay, sublabel, (cx - w2//2, cy), font, 0.4, TEXT_COLOR, 1)
    
    # 3. Draw Doors
    for i, door in enumerate(doors):
        bbox = door['bbox']
        x1, y1, x2, y2 = bbox
        center = tuple([int(c) for c in door['center']])
        
        # Draw bounding box
        cv2.rectangle(overlay, (x1, y1), (x2, y2), DOOR_COLOR, 2)
        
        # Draw center point
        cv2.circle(overlay, center, 4, DOOR_COLOR, -1)
        
        # Draw label
        width_m = door['width'] * scale_m_per_px
        height_m = door['height'] * scale_m_per_px
        label = f"D{i}"
        coords = f"({center[0]},{center[1]})"
        dims = f"{width_m:.2f}x{height_m:.2f}m"
        
        font = cv2.FONT_HERSHEY_SIMPLEX
        font_scale = 0.4
        thickness = 1
        
        y_offset = y1 - 10
        for text in [label, coords, dims]:
            (w, h), _ = cv2.getTextSize(text, font, font_scale, thickness)
            cv2.rectangle(overlay, (x1 - 2, y_offset - h - 2), (x1 + w + 2, y_offset + 2), TEXT_BG_COLOR, -1)
            cv2.putText(overlay, text, (x1, y_offset), font, font_scale, DOOR_COLOR, thickness)
            y_offset -= (h + 4)
    
    # 4. Draw Windows
    for i, window in enumerate(windows):
        bbox = window['bbox']
        x1, y1, x2, y2 = bbox
        center = tuple([int(c) for c in window['center']])
        
        # Draw bounding box
        cv2.rectangle(overlay, (x1, y1), (x2, y2), WINDOW_COLOR, 2)
        
        # Draw center point
        cv2.circle(overlay, center, 4, WINDOW_COLOR, -1)
        
        # Draw label
        width_m = window['width'] * scale_m_per_px
        height_m = window['height'] * scale_m_per_px
        label = f"Win{i}"
        coords = f"({center[0]},{center[1]})"
        dims = f"{width_m:.2f}x{height_m:.2f}m"
        
        font = cv2.FONT_HERSHEY_SIMPLEX
        font_scale = 0.4
        thickness = 1
        
        y_offset = y2 + 15
        for text in [label, coords, dims]:
            (w, h), _ = cv2.getTextSize(text, font, font_scale, thickness)
            cv2.rectangle(overlay, (x1 - 2, y_offset - h - 2), (x1 + w + 2, y_offset + 2), TEXT_BG_COLOR, -1)
            cv2.putText(overlay, text, (x1, y_offset), font, font_scale, WINDOW_COLOR, thickness)
            y_offset += (h + 4)
    
    # 5. Add legend
    legend_y = 30
    legend_x = 10
    
    cv2.rectangle(overlay, (legend_x, legend_y - 25), (legend_x + 200, legend_y + 85), (255, 255, 255), -1)
    cv2.rectangle(overlay, (legend_x, legend_y - 25), (legend_x + 200, legend_y + 85), (0, 0, 0), 1)
    
    font = cv2.FONT_HERSHEY_SIMPLEX
    font_scale = 0.5
    
    cv2.putText(overlay, "Legend:", (legend_x + 5, legend_y), font, font_scale, (0, 0, 0), 1)
    
    # Room
    cv2.rectangle(overlay, (legend_x + 10, legend_y + 10), (legend_x + 25, legend_y + 20), ROOM_COLOR, -1)
    cv2.putText(overlay, f"Rooms ({len(rooms)})", (legend_x + 30, legend_y + 20), font, 0.4, (0, 0, 0), 1)
    
    # Wall
    cv2.line(overlay, (legend_x + 10, legend_y + 35), (legend_x + 25, legend_y + 35), WALL_COLOR, 2)
    cv2.putText(overlay, f"Walls ({len(walls)})", (legend_x + 30, legend_y + 38), font, 0.4, (0, 0, 0), 1)
    
    # Door
    cv2.rectangle(overlay, (legend_x + 10, legend_y + 45), (legend_x + 25, legend_y + 55), DOOR_COLOR, 2)
    cv2.putText(overlay, f"Doors ({len(doors)})", (legend_x + 30, legend_y + 55), font, 0.4, (0, 0, 0), 1)
    
    # Window
    cv2.rectangle(overlay, (legend_x + 10, legend_y + 60), (legend_x + 25, legend_y + 70), WINDOW_COLOR, 2)
    cv2.putText(overlay, f"Windows ({len(windows)})", (legend_x + 30, legend_y + 72), font, 0.4, (0, 0, 0), 1)
    
    # Encode and return
    return _encode_png_data_url(overlay)
