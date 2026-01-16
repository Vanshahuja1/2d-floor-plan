"""
STEP 2: Wall Detection (Classical CV - NO ML)
Purpose: Extract wall geometry using Hough Line Transform
Tech: OpenCV edge detection + line detection
"""
import cv2
import numpy as np
from typing import Any
import math


def merge_collinear_lines(lines: list[dict], angle_threshold: float = 5.0, distance_threshold: float = 20.0) -> list[dict]:
    """
    Merge lines that are collinear (same angle and close together).
    
    Args:
        lines: List of line dicts with 'start', 'end', 'angle'
        angle_threshold: Max angle difference in degrees
        distance_threshold: Max distance between lines in pixels
    """
    if not lines:
        return []
    
    merged = []
    used = set()
    
    for i, line1 in enumerate(lines):
        if i in used:
            continue
            
        # Start a new merged line
        group = [line1]
        used.add(i)
        
        for j, line2 in enumerate(lines[i+1:], start=i+1):
            if j in used:
                continue
                
            # Check if collinear
            angle_diff = abs(line1['angle'] - line2['angle'])
            if angle_diff > 180:
                angle_diff = 360 - angle_diff
                
            if angle_diff < angle_threshold:
                # Check distance between lines
                # (simplified: check if endpoints are close)
                dist = min(
                    np.linalg.norm(np.array(line1['end']) - np.array(line2['start'])),
                    np.linalg.norm(np.array(line1['start']) - np.array(line2['end']))
                )
                
                if dist < distance_threshold:
                    group.append(line2)
                    used.add(j)
        
        # Merge the group into one line
        if len(group) == 1:
            merged.append(group[0])
        else:
            # Find extreme points
            all_points = []
            for line in group:
                all_points.append(line['start'])
                all_points.append(line['end'])
            
            all_points = np.array(all_points)
            
            # Find the two most distant points
            max_dist = 0
            p1, p2 = all_points[0], all_points[1]
            for i in range(len(all_points)):
                for j in range(i+1, len(all_points)):
                    dist = np.linalg.norm(all_points[i] - all_points[j])
                    if dist > max_dist:
                        max_dist = dist
                        p1, p2 = all_points[i], all_points[j]
            
            merged.append({
                'start': p1.tolist(),
                'end': p2.tolist(),
                'angle': line1['angle'],
                'length': max_dist
            })
    
    return merged


def detect_walls(preprocessed: dict[str, np.ndarray], wall_thickness_px: int) -> list[dict[str, Any]]:
    """
    Detect walls using Hough Line Transform.
    
    Args:
        preprocessed: Output from preprocess_blueprint()
        wall_thickness_px: Estimated wall thickness
        
    Returns:
        List of wall dicts with start, end, thickness, angle
    """
    cleaned = preprocessed['cleaned']
    
    # Edge detection
    edges = cv2.Canny(cleaned, 50, 150, apertureSize=3)
    
    # Hough Line Transform
    lines = cv2.HoughLinesP(
        edges,
        rho=1,
        theta=np.pi/180,
        threshold=150,
        minLineLength=100,
        maxLineGap=10
    )
    
    if lines is None:
        return []
    
    # Convert to structured format
    wall_lines = []
    for line in lines:
        x1, y1, x2, y2 = line[0]
        
        # Calculate angle
        angle = math.degrees(math.atan2(y2 - y1, x2 - x1))
        if angle < 0:
            angle += 180
        
        # Calculate length
        length = math.sqrt((x2 - x1)**2 + (y2 - y1)**2)
        
        wall_lines.append({
            'start': [int(x1), int(y1)],
            'end': [int(x2), int(y2)],
            'angle': round(angle, 2),
            'length': round(length, 2),
            'thickness_px': wall_thickness_px
        })
    
    # Merge collinear lines
    merged_walls = merge_collinear_lines(wall_lines)
    
    return merged_walls
