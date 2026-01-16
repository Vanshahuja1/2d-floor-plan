"""
STEP 6: Scale Conversion & JSON Export
Purpose: Convert pixel coordinates to real-world meters
Tech: Simple ratio multiplication
"""
from typing import Any


def apply_scale_conversion(
    rooms: list[dict],
    walls: list[dict],
    doors: list[dict],
    windows: list[dict],
    scale_m_per_px: float
) -> dict[str, Any]:
    """
    Convert all pixel measurements to meters and create final JSON.
    
    Args:
        rooms: Room data in pixels
        walls: Wall data in pixels
        doors: Door data in pixels
        windows: Window data in pixels
        scale_m_per_px: Conversion factor (meters per pixel)
        
    Returns:
        Complete JSON structure ready for 3D export
    """
    
    def px_to_m(value: float) -> float:
        """Convert pixels to meters"""
        return round(value * scale_m_per_px, 3)
    
    def point_px_to_m(point: list) -> list:
        """Convert [x, y] from pixels to meters"""
        return [px_to_m(point[0]), px_to_m(point[1])]
    
    # Convert rooms
    rooms_m = []
    for room in rooms:
        rooms_m.append({
            'id': room['id'],
            'polygon': [point_px_to_m(p) for p in room['polygon']],
            'area_m2': px_to_m(room['area_px']) * scale_m_per_px,  # Area needs double conversion
            'num_corners': room['num_corners']
        })
    
    # Convert walls
    walls_m = []
    for wall in walls:
        walls_m.append({
            'start': point_px_to_m(wall['start']),
            'end': point_px_to_m(wall['end']),
            'thickness_m': px_to_m(wall['thickness_px']),
            'length_m': px_to_m(wall['length']),
            'angle': wall['angle']
        })
    
    # Convert doors
    doors_m = []
    for door in doors:
        door_data = {
            'type': door.get('type', 'door'),
            'position': point_px_to_m(door['center']),
            'width_m': px_to_m(door['width']),
            'height_m': px_to_m(door['height']),
            'orientation': door['orientation'],
            'confidence': door['confidence']
        }
        
        if 'connects_rooms' in door and door['connects_rooms']:
            door_data['connects_rooms'] = door['connects_rooms']
        if 'nearest_wall_id' in door and door['nearest_wall_id'] >= 0:
            door_data['nearest_wall_id'] = door['nearest_wall_id']
            
        doors_m.append(door_data)
    
    # Convert windows
    windows_m = []
    for window in windows:
        window_data = {
            'type': window.get('type', 'window'),
            'position': point_px_to_m(window['center']),
            'width_m': px_to_m(window['width']),
            'height_m': px_to_m(window['height']),
            'orientation': window['orientation'],
            'confidence': window['confidence']
        }
        
        if 'room_id' in window and window['room_id']:
            window_data['room_id'] = window['room_id']
        if 'nearest_wall_id' in window and window['nearest_wall_id'] >= 0:
            window_data['nearest_wall_id'] = window['nearest_wall_id']
            
        windows_m.append(window_data)
    
    # Build final JSON
    return {
        'metadata': {
            'scale_m_per_px': scale_m_per_px,
            'total_rooms': len(rooms_m),
            'total_walls': len(walls_m),
            'total_doors': len(doors_m),
            'total_windows': len(windows_m)
        },
        'rooms': rooms_m,
        'walls': walls_m,
        'doors': doors_m,
        'windows': windows_m
    }
