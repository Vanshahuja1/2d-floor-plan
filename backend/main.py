from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
import cv2
import numpy as np

from services.room_detection import detect_rooms_and_overlay
from services.roboflow_service import infer_with_roboflow, process_roboflow_result
from services.yolov8_service import infer_yolo, process_yolo_result
from services.unified_detection import combine_room_and_element_detection
from services.hybrid import hybrid_floor_plan_analysis

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health() -> dict:
    return {"ok": True}


@app.post("/detect-rooms")
async def detect_rooms(
    image: UploadFile = File(...),
    scale_m_per_px: float = Form(...),
) -> dict:
    try:
        data = await image.read()
        arr = np.frombuffer(data, dtype=np.uint8)
        bgr = cv2.imdecode(arr, cv2.IMREAD_COLOR)
        if bgr is None:
            raise ValueError("Could not decode image")

        result = detect_rooms_and_overlay(bgr, scale_m_per_px=scale_m_per_px)
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/detect-roboflow")
async def detect_roboflow(
    image: UploadFile = File(...),
) -> dict:
    try:
        data = await image.read()
        arr = np.frombuffer(data, dtype=np.uint8)
        bgr = cv2.imdecode(arr, cv2.IMREAD_COLOR)
        if bgr is None:
            raise ValueError("Could not decode image")

        # Infer using Roboflow
        inference_result = infer_with_roboflow(bgr)
        # Process result and create overlay
        result = process_roboflow_result(bgr, inference_result)
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/detect-yolo")
async def detect_yolo(
    image: UploadFile = File(...),
) -> dict:
    try:
        data = await image.read()
        arr = np.frombuffer(data, dtype=np.uint8)
        bgr = cv2.imdecode(arr, cv2.IMREAD_COLOR)
        if bgr is None:
            raise ValueError("Could not decode image")

        # Infer using local YOLOv8
        inference_result = infer_yolo(bgr)
        # Process result and create overlay
        result = process_yolo_result(bgr, inference_result)
        return result
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/detect-unified")
async def detect_unified(
    image: UploadFile = File(...),
    scale_m_per_px: float = Form(...),
) -> dict:
    """
    Milestone 4: Best Accuracy - Combines OpenCV room detection + YOLO element detection
    Returns 3D-ready JSON with rooms, windows, doors, and walls.
    """
    try:
        data = await image.read()
        arr = np.frombuffer(data, dtype=np.uint8)
        bgr = cv2.imdecode(arr, cv2.IMREAD_COLOR)
        if bgr is None:
            raise ValueError("Could not decode image")

        # Combined detection
        result = combine_room_and_element_detection(bgr, scale_m_per_px=scale_m_per_px)
        return result
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/detect-hybrid")
async def detect_hybrid(
    image: UploadFile = File(...),
    scale_m_per_px: float = Form(...),
) -> dict:
    """
    🚀 PRODUCTION PIPELINE: Hybrid CV + DL
    
    Complete floor plan analysis using:
    - Classical CV for walls & rooms (Hough + Contours)
    - Deep Learning for doors & windows (YOLOv8)
    - Geometric association
    - Scale conversion to meters
    
    Returns: Production-ready JSON for 3D export
    """
    try:
        data = await image.read()
        arr = np.frombuffer(data, dtype=np.uint8)
        bgr = cv2.imdecode(arr, cv2.IMREAD_COLOR)
        if bgr is None:
            raise ValueError("Could not decode image")

        # Run hybrid pipeline
        result = hybrid_floor_plan_analysis(bgr, scale_m_per_px=scale_m_per_px)
        return result
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=400, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
