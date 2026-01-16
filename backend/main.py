from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
import cv2
import numpy as np

from services.room_detection import detect_rooms_and_overlay

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
