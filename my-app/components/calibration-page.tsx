"use client"

import { useState } from "react"
import ControlPanel from "./control-panel"
import CalibrationCanvas from "./calibration-canvas"

type DetectedRoom = {
  id: number
  polygon_px: Array<{ x: number; y: number }>
  edge_lengths_m: number[]
  perimeter_m: number
  area_m2: number
  area_px: number
}

type DetectRoomsResponse = {
  rooms: DetectedRoom[]
  overlay_png_data_url: string
  image_width_px: number
  image_height_px: number
}

export default function CalibrationPage() {
  const [uploadedImage, setUploadedImage] = useState<string | null>(null)
  const [wallLengthMeters, setWallLengthMeters] = useState<number | null>(null)
  const [pixelDistance, setPixelDistance] = useState<number | null>(null)
  const [scale, setScale] = useState<number | null>(null)
  const [detectingRooms, setDetectingRooms] = useState(false)
  const [detectRoomsError, setDetectRoomsError] = useState<string | null>(null)
  const [detectRoomsResult, setDetectRoomsResult] = useState<DetectRoomsResponse | null>(null)

  const handleImageUpload = (imageData: string) => {
    setUploadedImage(imageData)
    // Reset calibration when new image is uploaded
    setPixelDistance(null)
    setScale(null)
    setDetectRoomsError(null)
    setDetectRoomsResult(null)
  }

  const handleWallLengthChange = (length: number) => {
    setWallLengthMeters(length)
    setDetectRoomsError(null)
    setDetectRoomsResult(null)
    // Recalculate scale if both values are available
    if (pixelDistance && pixelDistance > 0 && length > 0) {
      setScale(length / pixelDistance)
    }
  }

  const handlePointsSelected = (distance: number) => {
    setPixelDistance(distance)
    setDetectRoomsError(null)
    setDetectRoomsResult(null)
    // Recalculate scale if both values are available
    if (wallLengthMeters && wallLengthMeters > 0 && distance > 0) {
      setScale(wallLengthMeters / distance)
    }
  }

  const handleDetectRooms = async () => {
    if (!uploadedImage || !scale || scale <= 0) return

    setDetectingRooms(true)
    setDetectRoomsError(null)

    try {
      const backendUrl = process.env.NEXT_PUBLIC_BACKEND_URL ?? "http://localhost:8000"
      const imageBlob = await (await fetch(uploadedImage)).blob()

      const form = new FormData()
      form.append("image", imageBlob, "floorplan.png")
      form.append("scale_m_per_px", String(scale))

      const res = await fetch(`${backendUrl}/detect-rooms`, {
        method: "POST",
        body: form,
      })

      if (!res.ok) {
        const text = await res.text()
        throw new Error(text || `Request failed: ${res.status}`)
      }

      const json = (await res.json()) as DetectRoomsResponse
      setDetectRoomsResult(json)
    } catch (e) {
      const message = e instanceof Error ? e.message : "Failed to detect rooms"
      setDetectRoomsError(message)
      setDetectRoomsResult(null)
    } finally {
      setDetectingRooms(false)
    }
  }

  return (
    <div className="min-h-screen bg-white">
      <div className="flex flex-col gap-6 p-6 md:flex-row md:gap-8 md:p-8">
        {/* Left Panel */}
        <div className="w-full md:w-96">
          <ControlPanel
            onImageUploadAction={handleImageUpload}
            onWallLengthChangeAction={handleWallLengthChange}
            wallLengthMeters={wallLengthMeters}
            pixelDistance={pixelDistance}
            scale={scale}
          />
        </div>

        {/* Right Panel */}
        <div className="flex-1">
          {uploadedImage ? (
            <div className="flex flex-col gap-4">
              <CalibrationCanvas imageData={uploadedImage} onPointsSelectedAction={handlePointsSelected} />

              <div className="flex flex-wrap items-center gap-3">
                <button
                  type="button"
                  onClick={handleDetectRooms}
                  disabled={!scale || detectingRooms}
                  className="rounded-lg border border-gray-300 bg-white px-4 py-2 text-sm font-medium text-gray-900 transition-colors hover:bg-gray-50 disabled:cursor-not-allowed disabled:opacity-60"
                >
                  {detectingRooms ? "Detecting rooms..." : "Detect rooms"}
                </button>

                {!scale && (
                  <p className="text-sm text-gray-600">Complete calibration first (select 2 points + enter wall length)</p>
                )}
              </div>

              {detectRoomsError && (
                <div className="rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-800">
                  {detectRoomsError}
                </div>
              )}

              {detectRoomsResult && (
                <div className="flex flex-col gap-6">
                  <div className="rounded-lg border border-gray-200 bg-white p-4">
                    <h3 className="text-sm font-medium text-gray-700">Detected Rooms Overlay</h3>
                    <div className="mt-3 overflow-hidden rounded-lg border border-gray-200 bg-gray-50">
                      <img
                        src={detectRoomsResult.overlay_png_data_url}
                        alt="Detected rooms overlay"
                        className="block h-auto w-full"
                      />
                    </div>
                  </div>

                  <div className="rounded-lg border border-gray-200 bg-white p-4">
                    <h3 className="text-sm font-medium text-gray-700">Rooms</h3>
                    {detectRoomsResult.rooms.length === 0 ? (
                      <p className="mt-2 text-sm text-gray-600">No rooms detected (try adjusting the input image or detection parameters).</p>
                    ) : (
                      <div className="mt-3 flex flex-col gap-3">
                        {detectRoomsResult.rooms.map((room) => (
                          <div key={room.id} className="rounded-lg bg-gray-50 p-3">
                            <div className="flex flex-wrap items-baseline justify-between gap-2">
                              <p className="text-sm font-medium text-gray-900">Room {room.id}</p>
                              <p className="text-xs text-gray-700">
                                Area: {room.area_m2.toFixed(2)} m² | Perimeter: {room.perimeter_m.toFixed(2)} m
                              </p>
                            </div>
                            <p className="mt-1 text-xs text-gray-700">
                              Edge lengths (m): {room.edge_lengths_m.map((v) => v.toFixed(2)).join(", ")}
                            </p>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                </div>
              )}
            </div>
          ) : (
            <div className="flex items-center justify-center rounded-lg border-2 border-dashed border-gray-300 bg-gray-50 p-12 text-center">
              <div>
                <p className="text-sm text-gray-600">Upload an image to begin calibration</p>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
