"""
STEP 3: Room Detection (Contour Logic)
Purpose: Find closed wall loops (rooms)
Tech: OpenCV contour detection
"""
import cv2
import numpy as np
from typing import Any


def detect_rooms(preprocessed: dict[str, np.ndarray], min_area_ratio: float = 0.001) -> list[dict[str, Any]]:
    """
    Detect rooms as closed polygons.
    
    Args:
        preprocessed: Output from preprocess_blueprint()
        min_area_ratio: Minimum room area as ratio of total image area
        
    Returns:
        List of room dicts with id, polygon, area_px
    """
    cleaned = preprocessed['cleaned']
    
    # Calculate minimum area
    total_area = cleaned.shape[0] * cleaned.shape[1]
    min_room_area = total_area * min_area_ratio
    
    # Find contours
    contours, _ = cv2.findContours(
        cleaned, 
        cv2.RETR_EXTERNAL, 
        cv2.CHAIN_APPROX_SIMPLE
    )
    
    rooms = []
    room_id = 0
    
    for cnt in contours:
        area = cv2.contourArea(cnt)
        
        # Filter by area
        if area < min_room_area:
            continue
        
        # Approximate polygon
        perimeter = cv2.arcLength(cnt, True)
        epsilon = 0.01 * perimeter
        approx = cv2.approxPolyDP(cnt, epsilon, True)
        
        # Must have at least 3 corners
        if len(approx) < 3:
            continue
        
        # Convert to simple list format
        polygon = [[int(p[0][0]), int(p[0][1])] for p in approx]
        
        rooms.append({
            'id': room_id,
            'polygon': polygon,
            'area_px': int(area),
            'num_corners': len(polygon)
        })
        
        room_id += 1
    
    return rooms


def point_inside_polygon(point: tuple[float, float], polygon: list[list[int]]) -> bool:
    """
    Check if a point is inside a polygon using OpenCV.
    """
    poly_np = np.array(polygon, dtype=np.int32)
    result = cv2.pointPolygonTest(poly_np, point, False)
    return result >= 0
