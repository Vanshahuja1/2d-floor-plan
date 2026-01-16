"""
STEP 4: Door & Window Detection (Pretrained DL)
Purpose: Detect architectural symbols using YOLO
Tech: YOLOv8 pretrained model
"""
import cv2
import numpy as np
from typing import Any
from services.yolov8_service import get_model


def detect_doors_windows(image_bgr: np.ndarray) -> dict[str, list[dict[str, Any]]]:
    """
    Detect doors and windows using pretrained YOLOv8.
    
    Returns:
        Dict with 'doors' and 'windows' lists
    """
    model = get_model()
    results = model(image_bgr)[0]
    
    doors = []
    windows = []
    
    for box in results.boxes:
        coords = box.xyxy[0].tolist()
        conf = float(box.conf[0])
        cls = int(box.cls[0])
        class_name = results.names[cls].lower()
        
        x1, y1, x2, y2 = [int(v) for v in coords]
        center_x = (x1 + x2) / 2
        center_y = (y1 + y2) / 2
        width = x2 - x1
        height = y2 - y1
        
        # Determine orientation (horizontal vs vertical)
        orientation = "horizontal" if width > height else "vertical"
        
        element = {
            'bbox': [x1, y1, x2, y2],
            'center': [center_x, center_y],
            'width': width,
            'height': height,
            'orientation': orientation,
            'confidence': round(conf, 3)
        }
        
        if 'door' in class_name:
            element['type'] = class_name  # door, sliding door, etc.
            doors.append(element)
        elif 'window' in class_name:
            element['type'] = class_name
            windows.append(element)
    
    return {
        'doors': doors,
        'windows': windows
    }


def calculate_orientation_angle(bbox: list[int]) -> float:
    """
    Calculate the orientation angle of a door/window.
    Returns angle in degrees (0-180).
    """
    x1, y1, x2, y2 = bbox
    width = x2 - x1
    height = y2 - y1
    
    if width > height:
        return 0.0  # Horizontal
    else:
        return 90.0  # Vertical
