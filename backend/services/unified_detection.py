import cv2
import numpy as np
from typing import Any
from services.room_detection import detect_rooms_and_overlay, RoomDetectionParams
from services.yolov8_service import infer_yolo


def combine_room_and_element_detection(
    image_bgr: np.ndarray,
    scale_m_per_px: float,
    params: RoomDetectionParams | None = None,
) -> dict[str, Any]:
    """
    Milestone 4: Combine OpenCV room detection with YOLO element detection
    to create a unified 3D-ready JSON structure.
    """
    
    # Step 1: Detect rooms using OpenCV (Milestone 2)
    room_result = detect_rooms_and_overlay(image_bgr, scale_m_per_px, params)
    
    # Step 2: Detect windows/doors using YOLO (Milestone 3)
    yolo_result = infer_yolo(image_bgr)
    
    # Step 3: Combine into unified structure
    unified_data = {
        "scale_m_per_px": scale_m_per_px,
        "image_dimensions": {
            "width_px": image_bgr.shape[1],
            "height_px": image_bgr.shape[0]
        },
        "rooms": []
    }
    
    # Process each room
    for room in room_result.get("rooms", []):
        room_id = f"room_{room['id']}"
        
        # Get room corners in meters
        corners_m = []
        for point in room["polygon_px"]:
            x_m = point["x"] * scale_m_per_px
            y_m = point["y"] * scale_m_per_px
            corners_m.append([round(x_m, 3), round(y_m, 3)])
        
        # Find windows and doors that belong to this room
        # (Check if element bounding box intersects with room polygon)
        room_windows = []
        room_doors = []
        
        room_polygon = np.array([[p["x"], p["y"]] for p in room["polygon_px"]], dtype=np.int32)
        
        for pred in yolo_result.get("predictions", []):
            element_class = pred["class"].lower()
            bbox = pred["bbox"]  # [x1, y1, x2, y2]
            
            # Calculate center of bounding box
            center_x = (bbox[0] + bbox[2]) / 2
            center_y = (bbox[1] + bbox[3]) / 2
            
            # Check if center is near the room boundary
            # (Using pointPolygonTest to check proximity)
            distance = cv2.pointPolygonTest(room_polygon, (center_x, center_y), True)
            
            # If element is on or very close to room boundary (within 20 pixels)
            if abs(distance) < 20:
                # Convert to meters
                x_m = center_x * scale_m_per_px
                y_m = center_y * scale_m_per_px
                width_m = (bbox[2] - bbox[0]) * scale_m_per_px
                height_m = (bbox[3] - bbox[1]) * scale_m_per_px
                
                element_data = {
                    "position": [round(x_m, 3), round(y_m, 3)],
                    "width": round(width_m, 3),
                    "height": round(height_m, 3),
                    "confidence": round(pred["confidence"], 3)
                }
                
                if "window" in element_class:
                    room_windows.append(element_data)
                elif "door" in element_class:
                    room_doors.append(element_data)
        
        # Build room entry
        room_entry = {
            "id": room_id,
            "corners": corners_m,
            "area_m2": round(room["area_m2"], 2),
            "windows": room_windows,
            "doors": room_doors
        }
        
        unified_data["rooms"].append(room_entry)
    
    # Also include standalone walls detected by YOLO
    walls = []
    for pred in yolo_result.get("predictions", []):
        if "wall" in pred["class"].lower():
            bbox = pred["bbox"]
            x1_m = bbox[0] * scale_m_per_px
            y1_m = bbox[1] * scale_m_per_px
            x2_m = bbox[2] * scale_m_per_px
            y2_m = bbox[3] * scale_m_per_px
            
            walls.append({
                "start": [round(x1_m, 3), round(y1_m, 3)],
                "end": [round(x2_m, 3), round(y2_m, 3)],
                "confidence": round(pred["confidence"], 3)
            })
    
    unified_data["walls"] = walls
    
    return unified_data
