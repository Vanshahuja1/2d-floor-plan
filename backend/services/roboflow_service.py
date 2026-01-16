import cv2
import numpy as np
import base64
from inference_sdk import InferenceHTTPClient
from typing import Any

CLIENT = InferenceHTTPClient(
    api_url="https://serverless.roboflow.com",
    api_key="ChqTzPG7IECVElj7R3A4"
)

def infer_with_roboflow(image_bgr: np.ndarray, model_id: str = "yolo-obb-1/1") -> dict[str, Any]:
    # Encode image to temporary file or base64 as inference-sdk might require it
    # inference-sdk can take numpy array directly usually, or path.
    # Let's save to a temp file or encode.
    
    # According to Roboflow docs, it can take numpy arrays.
    result = CLIENT.infer(image_bgr, model_id=model_id)
    return result

def _encode_png_data_url(image_bgr: np.ndarray) -> str:
    ok, buf = cv2.imencode(".png", image_bgr)
    if not ok:
        raise ValueError("Failed to encode overlay PNG")
    b64 = base64.b64encode(buf.tobytes()).decode("ascii")
    return f"data:image/png;base64,{b64}"

def process_roboflow_result(image_bgr: np.ndarray, result: dict[str, Any]) -> dict[str, Any]:
    """
    Process Roboflow OBB results and create an overlay.
    """
    overlay = image_bgr.copy()
    predictions = result.get("predictions", [])
    
    processed_predictions = []
    
    for i, pred in enumerate(predictions):
        # OBB predictions usually have x, y, width, height, and angle (or points)
        # Roboflow OBB format: {"x": ..., "y": ..., "width": ..., "height": ..., "angle": ..., "class": ..., "confidence": ...}
        
        x = pred.get("x")
        y = pred.get("y")
        w = pred.get("width")
        h = pred.get("height")
        angle = pred.get("angle")
        class_name = pred.get("class")
        confidence = pred.get("confidence")
        
        # Create rotated rectangle points
        rect = ((x, y), (w, h), angle)
        box = cv2.boxPoints(rect)
        box = np.int32(box)
        
        # Draw the OBB
        color = (0, 255, 0) # Green for all for now
        cv2.drawContours(overlay, [box], 0, color, 2)
        
        # Draw label
        label = f"{class_name} {confidence:.2f}"
        cv2.putText(overlay, label, (int(box[0][0]), int(box[0][1]) - 10), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)
        
        processed_predictions.append({
            "id": i,
            "class": class_name,
            "confidence": confidence,
            "points": [{"x": int(p[0]), "y": int(p[1])} for p in box]
        })
        
    return {
        "predictions": processed_predictions,
        "overlay_png_data_url": _encode_png_data_url(overlay),
        "total_detections": len(predictions)
    }
