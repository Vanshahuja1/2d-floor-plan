import cv2
import numpy as np
import base64
import os
import requests
from typing import Any
from ultralytics import YOLO

# Path to the local YOLOv8 model
MODEL_PATH = os.path.join(os.path.dirname(__file__), "..", "models", "best.pt")
MODEL_URL = "https://github.com/sanatladkat/floor-plan-object-detection/raw/main/best.pt"

_model = None

def get_model():
    global _model
    if _model is None:
        if not os.path.exists(MODEL_PATH):
            print(f"Model not found at {MODEL_PATH}. Downloading...")
            os.makedirs(os.path.dirname(MODEL_PATH), exist_ok=True)
            response = requests.get(MODEL_URL, stream=True)
            with open(MODEL_PATH, "wb") as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            print("Download complete.")
        _model = YOLO(MODEL_PATH)
    return _model

def infer_yolo(image_bgr: np.ndarray) -> dict[str, Any]:
    model = get_model()
    results = model(image_bgr)[0]
    
    predictions = []
    for box in results.boxes:
        # box.xyxy[0] -> (x1, y1, x2, y2)
        coords = box.xyxy[0].tolist()
        conf = float(box.conf[0])
        cls = int(box.cls[0])
        name = results.names[cls]
        
        predictions.append({
            "class": name,
            "confidence": conf,
            "bbox": [int(v) for v in coords]
        })
        
    return {
        "predictions": predictions,
        "names": results.names
    }

def _encode_png_data_url(image_bgr: np.ndarray) -> str:
    ok, buf = cv2.imencode(".png", image_bgr)
    if not ok:
        raise ValueError("Failed to encode overlay PNG")
    b64 = base64.b64encode(buf.tobytes()).decode("ascii")
    return f"data:image/png;base64,{b64}"

def process_yolo_result(image_bgr: np.ndarray, result: dict[str, Any]) -> dict[str, Any]:
    overlay = image_bgr.copy()
    
    # Colors for different classes
    colors = {
        "wall": (0, 0, 255),    # Red
        "door": (0, 255, 0),    # Green
        "window": (255, 0, 0),  # Blue
        "column": (255, 255, 0) # Cyan
    }
    
    for pred in result["predictions"]:
        x1, y1, x2, y2 = pred["bbox"]
        name = pred["class"]
        conf = pred["confidence"]
        
        color = colors.get(name.lower(), (0, 255, 255))
        cv2.rectangle(overlay, (x1, y1), (x2, y2), color, 2)
        
        label = f"{name} {conf:.2f}"
        cv2.putText(overlay, label, (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)
        
    return {
        "predictions": result["predictions"],
        "overlay_png_data_url": _encode_png_data_url(overlay),
        "total_detections": len(result["predictions"])
    }
