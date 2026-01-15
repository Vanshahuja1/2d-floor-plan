"use client"

import { useState } from "react"
import ControlPanel from "./control-panel"
import CalibrationCanvas from "./calibration-canvas"

export default function CalibrationPage() {
  const [uploadedImage, setUploadedImage] = useState<string | null>(null)
  const [wallLengthMeters, setWallLengthMeters] = useState<number | null>(null)
  const [pixelDistance, setPixelDistance] = useState<number | null>(null)
  const [scale, setScale] = useState<number | null>(null)

  const handleImageUpload = (imageData: string) => {
    setUploadedImage(imageData)
    // Reset calibration when new image is uploaded
    setPixelDistance(null)
    setScale(null)
  }

  const handleWallLengthChange = (length: number) => {
    setWallLengthMeters(length)
    // Recalculate scale if both values are available
    if (pixelDistance && pixelDistance > 0 && length > 0) {
      setScale(length / pixelDistance)
    }
  }

  const handlePointsSelected = (distance: number) => {
    setPixelDistance(distance)
    // Recalculate scale if both values are available
    if (wallLengthMeters && wallLengthMeters > 0 && distance > 0) {
      setScale(wallLengthMeters / distance)
    }
  }

  return (
    <div className="min-h-screen bg-white">
      <div className="flex flex-col gap-6 p-6 md:flex-row md:gap-8 md:p-8">
        {/* Left Panel */}
        <div className="w-full md:w-96">
          <ControlPanel
            onImageUpload={handleImageUpload}
            onWallLengthChange={handleWallLengthChange}
            wallLengthMeters={wallLengthMeters}
            pixelDistance={pixelDistance}
            scale={scale}
          />
        </div>

        {/* Right Panel */}
        <div className="flex-1">
          {uploadedImage ? (
            <CalibrationCanvas imageData={uploadedImage} onPointsSelected={handlePointsSelected} />
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
