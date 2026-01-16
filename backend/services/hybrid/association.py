"""
STEP 5: Associate Doors/Windows with Walls & Rooms
Purpose: Link detected elements to their parent structures
Tech: Geometric proximity analysis
"""
import numpy as np
from typing import Any
import math


def point_to_line_distance(point: tuple[float, float], line_start: list, line_end: list) -> float:
    """
    Calculate perpendicular distance from point to line segment.
    """
    px, py = point
    x1, y1 = line_start
    x2, y2 = line_end
    
    # Line segment length
    line_len = math.sqrt((x2 - x1)**2 + (y2 - y1)**2)
    if line_len == 0:
        return math.sqrt((px - x1)**2 + (py - y1)**2)
    
    # Calculate perpendicular distance
    t = max(0, min(1, ((px - x1) * (x2 - x1) + (py - y1) * (y2 - y1)) / (line_len ** 2)))
    proj_x = x1 + t * (x2 - x1)
    proj_y = y1 + t * (y2 - y1)
    
    return math.sqrt((px - proj_x)**2 + (py - proj_y)**2)


def associate_elements_with_walls(
    doors: list[dict],
    windows: list[dict],
    walls: list[dict],
    max_distance: float = 15.0
) -> tuple[list[dict], list[dict]]:
    """
    Associate doors and windows with nearest walls.
    
    Args:
        doors: List of door dicts
        windows: List of window dicts
        walls: List of wall dicts
        max_distance: Maximum distance to consider (pixels)
        
    Returns:
        Updated (doors, windows) with 'nearest_wall_id' field
    """
    def find_nearest_wall(element: dict, walls: list[dict]) -> int:
        center = tuple(element['center'])
        min_dist = float('inf')
        nearest_id = -1
        
        for i, wall in enumerate(walls):
            dist = point_to_line_distance(center, wall['start'], wall['end'])
            if dist < min_dist:
                min_dist = dist
                nearest_id = i
        
        return nearest_id if min_dist < max_distance else -1
    
    # Associate doors
    for door in doors:
        door['nearest_wall_id'] = find_nearest_wall(door, walls)
    
    # Associate windows
    for window in windows:
        window['nearest_wall_id'] = find_nearest_wall(window, walls)
    
    return doors, windows


def associate_elements_with_rooms(
    doors: list[dict],
    windows: list[dict],
    rooms: list[dict]
) -> tuple[list[dict], list[dict]]:
    """
    Determine which room(s) each door/window connects.
    
    Returns:
        Updated (doors, windows) with 'connects_rooms' field
    """
    from .room_detection import point_inside_polygon
    
    def find_connected_rooms(element: dict, rooms: list[dict]) -> list[int]:
        center = tuple(element['center'])
        connected = []
        
        for room in rooms:
            # Check if element is on room boundary (close to polygon edge)
            poly = np.array(room['polygon'], dtype=np.int32)
            distance = abs(cv2.pointPolygonTest(poly, center, True))
            
            # If very close to boundary (within 20 pixels)
            if distance < 20:
                connected.append(room['id'])
        
        return connected
    
    # Associate doors
    for door in doors:
        door['connects_rooms'] = find_connected_rooms(door, rooms)
    
    # Associate windows  
    for window in windows:
        window['room_id'] = find_connected_rooms(window, rooms)
    
    return doors, windows


import cv2  # Import needed for pointPolygonTest
