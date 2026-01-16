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

type RoboflowPrediction = {
  id: number
  class: string
  confidence: number
  points: Array<{ x: number; y: number }>
}

type RoboflowResponse = {
  predictions: RoboflowPrediction[]
  overlay_png_data_url: string
  total_detections: number
}

type YoloPrediction = {
  class: string
  confidence: number
  bbox: [number, number, number, number]
}

type YoloResponse = {
  predictions: YoloPrediction[]
  overlay_png_data_url: string
  total_detections: number
}

type UnifiedResponse = {
  scale_m_per_px: number
  image_dimensions: { width_px: number; height_px: number }
  rooms: Array<{
    id: string
    corners: number[][]
    area_m2: number
    windows: Array<{ position: number[]; width: number; height: number; confidence: number }>
    doors: Array<{ position: number[]; width: number; height: number; confidence: number }>
  }>
  walls: Array<{ start: number[]; end: number[]; confidence: number }>
}

type HybridResponse = {
  metadata: {
    scale_m_per_px: number
    total_rooms: number
    total_walls: number
    total_doors: number
    total_windows: number
  }
  rooms: Array<{
    id: number
    polygon: number[][]
    area_m2: number
    num_corners: number
  }>
  walls: Array<{
    start: number[]
    end: number[]
    thickness_m: number
    length_m: number
    angle: number
  }>
  doors: Array<{
    type: string
    position: number[]
    width_m: number
    height_m: number
    orientation: string
    confidence: number
    connects_rooms?: number[]
    nearest_wall_id?: number
  }>
  windows: Array<{
    type: string
    position: number[]
    width_m: number
    height_m: number
    orientation: string
    confidence: number
    room_id?: number[]
    nearest_wall_id?: number
  }>
  annotated_image: string
}

export default function CalibrationPage() {
  const [uploadedImage, setUploadedImage] = useState<string | null>(null)
  const [wallLengthMeters, setWallLengthMeters] = useState<number | null>(null)
  const [pixelDistance, setPixelDistance] = useState<number | null>(null)
  const [scale, setScale] = useState<number | null>(null)
  const [detectingRooms, setDetectingRooms] = useState(false)
  const [detectRoomsError, setDetectRoomsError] = useState<string | null>(null)
  const [detectRoomsResult, setDetectRoomsResult] = useState<DetectRoomsResponse | null>(null)
  const [detectingRoboflow, setDetectingRoboflow] = useState(false)
  const [roboflowResult, setRoboflowResult] = useState<RoboflowResponse | null>(null)
  const [detectingYolo, setDetectingYolo] = useState(false)
  const [yoloResult, setYoloResult] = useState<YoloResponse | null>(null)
  const [detectingUnified, setDetectingUnified] = useState(false)
  const [unifiedResult, setUnifiedResult] = useState<UnifiedResponse | null>(null)
  const [detectingHybrid, setDetectingHybrid] = useState(false)
  const [hybridResult, setHybridResult] = useState<HybridResponse | null>(null)

  const handleImageUpload = (imageData: string) => {
    setUploadedImage(imageData)
    // Reset calibration when new image is uploaded
    setPixelDistance(null)
    setScale(null)
    setDetectRoomsError(null)
    setDetectRoomsResult(null)
    setRoboflowResult(null)
    setYoloResult(null)
    setUnifiedResult(null)
    setHybridResult(null)
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

  const handleRoboflowDetect = async () => {
    if (!uploadedImage) return

    setDetectingRoboflow(true)
    setDetectRoomsError(null)

    try {
      const backendUrl = process.env.NEXT_PUBLIC_BACKEND_URL ?? "http://localhost:8000"
      const imageBlob = await (await fetch(uploadedImage)).blob()

      const form = new FormData()
      form.append("image", imageBlob, "floorplan.png")

      const res = await fetch(`${backendUrl}/detect-roboflow`, {
        method: "POST",
        body: form,
      })

      if (!res.ok) {
        const text = await res.text()
        throw new Error(text || `Request failed: ${res.status}`)
      }

      const json = (await res.json()) as RoboflowResponse
      setRoboflowResult(json)
    } catch (e) {
      const message = e instanceof Error ? e.message : "Failed to detect with Roboflow"
      setDetectRoomsError(message)
      setRoboflowResult(null)
    } finally {
      setDetectingRoboflow(false)
    }
  }

  const handleYoloDetect = async () => {
    if (!uploadedImage) return

    setDetectingYolo(true)
    setDetectRoomsError(null)

    try {
      const backendUrl = process.env.NEXT_PUBLIC_BACKEND_URL ?? "http://localhost:8000"
      const imageBlob = await (await fetch(uploadedImage)).blob()

      const form = new FormData()
      form.append("image", imageBlob, "floorplan.png")

      const res = await fetch(`${backendUrl}/detect-yolo`, {
        method: "POST",
        body: form,
      })

      if (!res.ok) {
        const text = await res.text()
        throw new Error(text || `Request failed: ${res.status}`)
      }

      const json = (await res.json()) as YoloResponse
      setYoloResult(json)
    } catch (e) {
      const message = e instanceof Error ? e.message : "Failed to detect with YOLO"
      setDetectRoomsError(message)
      setYoloResult(null)
    } finally {
      setDetectingYolo(false)
    }
  }

  const handleUnifiedDetect = async () => {
    if (!uploadedImage || !scale || scale <= 0) return

    setDetectingUnified(true)
    setDetectRoomsError(null)

    try {
      const backendUrl = process.env.NEXT_PUBLIC_BACKEND_URL ?? "http://localhost:8000"
      const imageBlob = await (await fetch(uploadedImage)).blob()

      const form = new FormData()
      form.append("image", imageBlob, "floorplan.png")
      form.append("scale_m_per_px", String(scale))

      const res = await fetch(`${backendUrl}/detect-unified`, {
        method: "POST",
        body: form,
      })

      if (!res.ok) {
        const text = await res.text()
        throw new Error(text || `Request failed: ${res.status}`)
      }

      const json = (await res.json()) as UnifiedResponse
      setUnifiedResult(json)
    } catch (e) {
      const message = e instanceof Error ? e.message : "Failed unified detection"
      setDetectRoomsError(message)
      setUnifiedResult(null)
    } finally {
      setDetectingUnified(false)
    }
  }

  const handleHybridDetect = async () => {
    if (!uploadedImage || !scale || scale <= 0) return

    setDetectingHybrid(true)
    setDetectRoomsError(null)

    try {
      const backendUrl = process.env.NEXT_PUBLIC_BACKEND_URL ?? "http://localhost:8000"
      const imageBlob = await (await fetch(uploadedImage)).blob()

      const form = new FormData()
      form.append("image", imageBlob, "floorplan.png")
      form.append("scale_m_per_px", String(scale))

      const res = await fetch(`${backendUrl}/detect-hybrid`, {
        method: "POST",
        body: form,
      })

      if (!res.ok) {
        const text = await res.text()
        throw new Error(text || `Request failed: ${res.status}`)
      }

      const json = (await res.json()) as HybridResponse
      setHybridResult(json)
    } catch (e) {
      const message = e instanceof Error ? e.message : "Failed hybrid detection"
      setDetectRoomsError(message)
      setHybridResult(null)
    } finally {
      setDetectingHybrid(false)
    }
  }

  const handleCompareAll = async () => {
    if (scale) handleDetectRooms()
    handleRoboflowDetect()
    handleYoloDetect()
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
            <div className="flex flex-col gap-8">
              <div className="flex flex-col gap-4">
                <CalibrationCanvas imageData={uploadedImage} onPointsSelectedAction={handlePointsSelected} />

                <div className="flex flex-wrap items-center gap-3">
                  <button
                    type="button"
                    onClick={handleDetectRooms}
                    disabled={!scale || detectingRooms}
                    className="rounded-lg border border-gray-300 bg-white px-4 py-2 text-sm font-medium text-gray-900 transition-colors hover:bg-gray-50 disabled:cursor-not-allowed disabled:opacity-60"
                  >
                    {detectingRooms ? "Detecting rooms..." : "OpenCV Rooms"}
                  </button>

                  <button
                    type="button"
                    onClick={handleRoboflowDetect}
                    disabled={detectingRoboflow}
                    className="rounded-lg border border-indigo-300 bg-indigo-50 px-4 py-2 text-sm font-medium text-indigo-900 transition-colors hover:bg-indigo-100 disabled:cursor-not-allowed disabled:opacity-60"
                  >
                    {detectingRoboflow ? "Roboflow..." : "Roboflow"}
                  </button>

                  <button
                    type="button"
                    onClick={handleYoloDetect}
                    disabled={detectingYolo}
                    className="rounded-lg border border-orange-300 bg-orange-50 px-4 py-2 text-sm font-medium text-orange-900 transition-colors hover:bg-orange-100 disabled:cursor-not-allowed disabled:opacity-60"
                  >
                    {detectingYolo ? "YOLOv8..." : "Local YOLOv8"}
                  </button>

                  <button
                    type="button"
                    onClick={handleCompareAll}
                    disabled={detectingRooms || detectingRoboflow || detectingYolo}
                    className="rounded-lg border border-pink-300 bg-pink-50 px-4 py-2 text-sm font-medium text-pink-900 transition-colors hover:bg-pink-100 disabled:cursor-not-allowed disabled:opacity-60 shadow-sm hover:shadow"
                  >
                    Compare All
                  </button>

                  <button
                    type="button"
                    onClick={handleUnifiedDetect}
                    disabled={!scale || detectingUnified}
                    className="rounded-lg border-2 border-green-500 bg-green-50 px-6 py-2 text-sm font-bold text-green-900 transition-colors hover:bg-green-100 disabled:cursor-not-allowed disabled:opacity-60 shadow-md hover:shadow-lg"
                  >
                    {detectingUnified ? "Processing..." : "🎯 Best Accuracy (Unified)"}
                  </button>

                  <button
                    type="button"
                    onClick={handleHybridDetect}
                    disabled={!scale || detectingHybrid}
                    className="rounded-lg border-2 border-purple-600 bg-gradient-to-r from-purple-50 to-indigo-50 px-6 py-2 text-sm font-bold text-purple-900 transition-all hover:from-purple-100 hover:to-indigo-100 disabled:cursor-not-allowed disabled:opacity-60 shadow-lg hover:shadow-xl"
                  >
                    {detectingHybrid ? "Processing..." : "🚀 PRODUCTION (Hybrid CV+DL)"}
                  </button>

                  {!scale && (
                    <p className="text-xs text-gray-400">Calibration needed for OpenCV Rooms</p>
                  )}
                </div>

                {detectRoomsError && (
                  <div className="rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-800">
                    {detectRoomsError}
                  </div>
                )}
              </div>

              {hybridResult && (
                <div className="rounded-lg border-2 border-purple-600 bg-gradient-to-br from-purple-50 to-indigo-50 p-6">
                  <div className="flex items-center justify-between mb-4">
                    <h3 className="text-2xl font-bold text-purple-900">🚀 PRODUCTION PIPELINE RESULT</h3>
                    <button
                      onClick={() => {
                        const blob = new Blob([JSON.stringify(hybridResult, null, 2)], { type: 'application/json' })
                        const url = URL.createObjectURL(blob)
                        const a = document.createElement('a')
                        a.href = url
                        a.download = 'floor_plan_production.json'
                        a.click()
                      }}
                      className="px-4 py-2 bg-purple-600 text-white text-sm font-semibold rounded hover:bg-purple-700 shadow-md"
                    >
                      📥 Download JSON
                    </button>
                  </div>

                  {/* Annotated Image - FIRST AND PROMINENT */}
                  <div className="mb-6 bg-white rounded-lg p-4 border border-purple-200 shadow-lg">
                    <h4 className="text-lg font-bold text-purple-900 mb-3">📸 Annotated Floor Plan</h4>
                    <div className="overflow-hidden rounded-lg border-2 border-purple-300 shadow-lg">
                      <img
                        src={hybridResult.annotated_image}
                        alt="Annotated floor plan with all detections"
                        className="w-full h-auto"
                      />
                    </div>
                    <p className="text-sm text-purple-700 mt-2 font-semibold">
                      ✨ All elements labeled with coordinates and dimensions
                    </p>
                  </div>

                  {/* Stats Grid - Compact */}
                  <div className="grid grid-cols-4 gap-3 mb-4">
                    <div className="bg-gradient-to-br from-blue-50 to-blue-100 p-3 rounded-lg border border-blue-200 text-center">
                      <p className="text-xs text-blue-700 font-semibold">Rooms</p>
                      <p className="text-2xl font-bold text-blue-900">{hybridResult.metadata.total_rooms}</p>
                    </div>
                    <div className="bg-gradient-to-br from-red-50 to-red-100 p-3 rounded-lg border border-red-200 text-center">
                      <p className="text-xs text-red-700 font-semibold">Walls</p>
                      <p className="text-2xl font-bold text-red-900">{hybridResult.metadata.total_walls}</p>
                    </div>
                    <div className="bg-gradient-to-br from-orange-50 to-orange-100 p-3 rounded-lg border border-orange-200 text-center">
                      <p className="text-xs text-orange-700 font-semibold">Doors</p>
                      <p className="text-2xl font-bold text-orange-900">{hybridResult.metadata.total_doors}</p>
                    </div>
                    <div className="bg-gradient-to-br from-cyan-50 to-cyan-100 p-3 rounded-lg border border-cyan-200 text-center">
                      <p className="text-xs text-cyan-700 font-semibold">Windows</p>
                      <p className="text-2xl font-bold text-cyan-900">{hybridResult.metadata.total_windows}</p>
                    </div>
                  </div>

                  {/* Pipeline Info - Compact */}
                  <details className="mb-3">
                    <summary className="cursor-pointer p-3 bg-purple-100 rounded border border-purple-300 font-semibold text-purple-900 hover:bg-purple-200">
                      ✨ Pipeline Breakdown (Click to expand)
                    </summary>
                    <div className="mt-2 p-3 bg-white rounded border border-purple-200">
                      <ul className="text-xs text-purple-800 space-y-1">
                        <li>✅ <strong>Preprocessing:</strong> Adaptive threshold + noise removal</li>
                        <li>✅ <strong>Walls:</strong> Hough Line Transform (Classical CV)</li>
                        <li>✅ <strong>Rooms:</strong> Contour detection + polygon simplification</li>
                        <li>✅ <strong>Doors/Windows:</strong> YOLOv8 pretrained model</li>
                        <li>✅ <strong>Association:</strong> Geometric proximity matching</li>
                        <li>✅ <strong>Scale:</strong> Pixel → Meter conversion</li>
                      </ul>
                    </div>
                  </details>

                  {/* JSON Data - Collapsible */}
                  <details>
                    <summary className="cursor-pointer p-3 bg-gray-100 rounded border border-gray-300 font-semibold text-gray-900 hover:bg-gray-200">
                      📄 View Full JSON Data (Click to expand)
                    </summary>
                    <pre className="mt-2 bg-gray-900 text-green-400 p-4 rounded text-xs overflow-auto max-h-96 font-mono">
                      {JSON.stringify({
                        ...hybridResult,
                        annotated_image: "[Base64 image data - see above for visual]"
                      }, null, 2)}
                    </pre>
                  </details>
                </div>
              )}

              {unifiedResult && (
                <div className="rounded-lg border-2 border-green-500 bg-green-50 p-6">
                  <div className="flex items-center gap-2 mb-4">
                    <h3 className="text-xl font-bold text-green-900">🎯 Best Accuracy Result (3D-Ready JSON)</h3>
                  </div>

                  <div className="bg-white rounded-lg p-4 border border-green-200">
                    <div className="flex justify-between items-center mb-2">
                      <p className="text-sm font-semibold text-gray-700">Unified Detection Output</p>
                      <button
                        onClick={() => {
                          const blob = new Blob([JSON.stringify(unifiedResult, null, 2)], { type: 'application/json' })
                          const url = URL.createObjectURL(blob)
                          const a = document.createElement('a')
                          a.href = url
                          a.download = 'floor_plan_3d_ready.json'
                          a.click()
                        }}
                        className="px-3 py-1 bg-green-600 text-white text-xs rounded hover:bg-green-700"
                      >
                        Download JSON
                      </button>
                    </div>

                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
                      <div className="bg-gray-50 p-3 rounded">
                        <p className="text-xs text-gray-600">Rooms Detected</p>
                        <p className="text-2xl font-bold text-gray-900">{unifiedResult.rooms.length}</p>
                      </div>
                      <div className="bg-gray-50 p-3 rounded">
                        <p className="text-xs text-gray-600">Total Windows</p>
                        <p className="text-2xl font-bold text-blue-600">
                          {unifiedResult.rooms.reduce((sum, r) => sum + r.windows.length, 0)}
                        </p>
                      </div>
                      <div className="bg-gray-50 p-3 rounded">
                        <p className="text-xs text-gray-600">Total Doors</p>
                        <p className="text-2xl font-bold text-orange-600">
                          {unifiedResult.rooms.reduce((sum, r) => sum + r.doors.length, 0)}
                        </p>
                      </div>
                    </div>

                    <pre className="bg-gray-900 text-green-400 p-4 rounded text-xs overflow-auto max-h-96 font-mono">
                      {JSON.stringify(unifiedResult, null, 2)}
                    </pre>
                  </div>
                </div>
              )}

              {(detectRoomsResult || roboflowResult || yoloResult) && (
                <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
                  {/* OpenCV Column */}
                  <div className="flex flex-col gap-4">
                    <h3 className="text-lg font-semibold text-gray-800 border-b pb-2">OpenCV (Traditional)</h3>
                    {detectingRooms ? (
                      <div className="flex h-48 items-center justify-center rounded-lg border bg-gray-50">Processing...</div>
                    ) : detectRoomsResult ? (
                      <div className="flex flex-col gap-3">
                        <div className="overflow-hidden rounded-lg border bg-white shadow-sm">
                          <img src={detectRoomsResult.overlay_png_data_url} alt="OpenCV" className="w-full" />
                        </div>
                        <div className="rounded-lg bg-gray-50 p-3 text-xs">
                          <p className="font-bold">Rooms: {detectRoomsResult.rooms.length}</p>
                          <p className="mt-1 text-gray-600">Pure Image Processing</p>
                        </div>
                      </div>
                    ) : (
                      <p className="text-sm text-gray-400">Run OpenCV detection to see results</p>
                    )}
                  </div>

                  {/* Roboflow Column */}
                  <div className="flex flex-col gap-4">
                    <h3 className="text-lg font-semibold text-indigo-800 border-b pb-2 border-indigo-100">Roboflow (Hosted)</h3>
                    {detectingRoboflow ? (
                      <div className="flex h-48 items-center justify-center rounded-lg border bg-indigo-50">Inference...</div>
                    ) : roboflowResult ? (
                      <div className="flex flex-col gap-3">
                        <div className="overflow-hidden rounded-lg border border-indigo-200 bg-white shadow-sm">
                          <img src={roboflowResult.overlay_png_data_url} alt="Roboflow" className="w-full" />
                        </div>
                        <div className="rounded-lg bg-indigo-50 p-3 text-xs">
                          <p className="font-bold text-indigo-900">Detections: {roboflowResult.total_detections}</p>
                          <div className="mt-1 flex flex-wrap gap-1">
                            {roboflowResult.predictions.slice(0, 5).map((p, i) => (
                              <span key={i} className="rounded bg-white px-1 py-0.5 border border-indigo-100">{p.class}</span>
                            ))}
                          </div>
                        </div>
                      </div>
                    ) : (
                      <p className="text-sm text-gray-400">Run Roboflow detection to see results</p>
                    )}
                  </div>

                  {/* YOLO Column */}
                  <div className="flex flex-col gap-4">
                    <h3 className="text-lg font-semibold text-orange-800 border-b pb-2 border-orange-100">YOLOv8 (Local)</h3>
                    {detectingYolo ? (
                      <div className="flex h-48 items-center justify-center rounded-lg border bg-orange-50">Inference...</div>
                    ) : yoloResult ? (
                      <div className="flex flex-col gap-3">
                        <div className="overflow-hidden rounded-lg border border-orange-200 bg-white shadow-sm">
                          <img src={yoloResult.overlay_png_data_url} alt="YOLOv8" className="w-full" />
                        </div>
                        <div className="rounded-lg bg-orange-50 p-3 text-xs">
                          <p className="font-bold text-orange-900">Detections: {yoloResult.total_detections}</p>
                          <div className="mt-1 flex flex-wrap gap-1">
                            {yoloResult.predictions.slice(0, 5).map((p, i) => (
                              <span key={i} className="rounded bg-white px-1 py-0.5 border border-orange-100">{p.class}</span>
                            ))}
                          </div>
                        </div>
                      </div>
                    ) : (
                      <p className="text-sm text-gray-400">Run YOLOv8 detection to see results</p>
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
