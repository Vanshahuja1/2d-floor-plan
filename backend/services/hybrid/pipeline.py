"""
HYBRID CV + DL PIPELINE
Complete floor plan analysis system combining:
- Classical Computer Vision (walls, rooms)
- Deep Learning (doors, windows)
"""
import cv2
import numpy as np
from typing import Any

from .preprocessing import preprocess_blueprint, estimate_wall_thickness
from .wall_detection import detect_walls
from .room_detection import detect_rooms
from .element_detection import detect_doors_windows
from .association import associate_elements_with_walls, associate_elements_with_rooms
from .scale_conversion import apply_scale_conversion
from .visualization import create_annotated_overlay


def hybrid_floor_plan_analysis(
    image_bgr: np.ndarray,
    scale_m_per_px: float
) -> dict[str, Any]:
    """
    Complete hybrid pipeline for floor plan analysis.
    
    Pipeline:
        1. Preprocessing (OpenCV)
        2. Wall Detection (Hough Transform)
        3. Room Detection (Contours)
        4. Door/Window Detection (YOLOv8)
        5. Association (Geometric matching)
        6. Scale Conversion (Pixel → Meter)
        7. Visualization (Annotated overlay)
    
    Args:
        image_bgr: Input floor plan image (BGR format)
        scale_m_per_px: Conversion factor (meters per pixel)
        
    Returns:
        Complete JSON structure with rooms, walls, doors, windows + annotated image
    """
    
    # STEP 1: Preprocessing
    preprocessed = preprocess_blueprint(image_bgr)
    wall_thickness = estimate_wall_thickness(preprocessed['cleaned'])
    
    # STEP 2: Wall Detection (Classical CV)
    walls = detect_walls(preprocessed, wall_thickness)
    
    # STEP 3: Room Detection (Contour Logic)
    rooms = detect_rooms(preprocessed)
    
    # STEP 4: Door & Window Detection (Pretrained DL)
    elements = detect_doors_windows(image_bgr)
    doors = elements['doors']
    windows = elements['windows']
    
    # STEP 5: Association
    doors, windows = associate_elements_with_walls(doors, windows, walls)
    doors, windows = associate_elements_with_rooms(doors, windows, rooms)
    
    # STEP 6: Scale Conversion & JSON Export
    final_json = apply_scale_conversion(rooms, walls, doors, windows, scale_m_per_px)
    
    # STEP 7: Create Annotated Overlay
    overlay_image = create_annotated_overlay(image_bgr, rooms, walls, doors, windows, scale_m_per_px)
    final_json['annotated_image'] = overlay_image
    
    return final_json
