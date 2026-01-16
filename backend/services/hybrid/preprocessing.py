"""
STEP 1: Image Preprocessing
Purpose: Make blueprint machine-readable
Tech: OpenCV
"""
import cv2
import numpy as np
from typing import Any


def preprocess_blueprint(image_bgr: np.ndarray) -> dict[str, np.ndarray]:
    """
    Preprocess floor plan image for optimal detection.
    
    Returns:
        dict with 'grayscale', 'binary', 'cleaned' versions
    """
    # Convert to grayscale
    gray = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2GRAY)
    
    # Adaptive threshold (handles faded scans)
    binary = cv2.adaptiveThreshold(
        gray, 255,
        cv2.ADAPTIVE_THRESH_MEAN_C,
        cv2.THRESH_BINARY_INV, 15, 3
    )
    
    # Remove text & furniture noise
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
    cleaned = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel)
    
    # Additional noise removal
    cleaned = cv2.morphologyEx(cleaned, cv2.MORPH_OPEN, kernel, iterations=1)
    
    return {
        "grayscale": gray,
        "binary": binary,
        "cleaned": cleaned
    }


def estimate_wall_thickness(binary_image: np.ndarray) -> int:
    """
    Estimate average wall thickness in pixels.
    Uses morphological operations to find typical wall width.
    """
    # Find horizontal and vertical structures
    horizontal_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (40, 1))
    vertical_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (1, 40))
    
    horizontal = cv2.morphologyEx(binary_image, cv2.MORPH_OPEN, horizontal_kernel)
    vertical = cv2.morphologyEx(binary_image, cv2.MORPH_OPEN, vertical_kernel)
    
    # Combine
    walls = cv2.bitwise_or(horizontal, vertical)
    
    # Find contours and measure widths
    contours, _ = cv2.findContours(walls, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    widths = []
    for cnt in contours:
        x, y, w, h = cv2.boundingRect(cnt)
        # Wall thickness is the smaller dimension
        thickness = min(w, h)
        if 5 < thickness < 50:  # Reasonable wall thickness range
            widths.append(thickness)
    
    if widths:
        return int(np.median(widths))
    return 12  # Default fallback
