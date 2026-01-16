"use client"

import type React from "react"

import { useEffect, useRef, useState } from "react"
import { RotateCcw } from "lucide-react"

interface CalibrationCanvasProps {
  imageData: string
  onPointsSelectedAction: (distance: number) => void
}

export default function CalibrationCanvas({ imageData, onPointsSelectedAction }: CalibrationCanvasProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null)
  const [points, setPoints] = useState<Array<{ x: number; y: number }>>([])
  const [image, setImage] = useState<HTMLImageElement | null>(null)

  // Load image
  useEffect(() => {
    const img = new Image()
    img.src = imageData
    img.onload = () => {
      setImage(img)
      setPoints([]) // Reset points on new image
    }
  }, [imageData])

  // Draw canvas
  useEffect(() => {
    const canvas = canvasRef.current
    if (!canvas || !image) return

    // Set canvas size based on image dimensions
    const maxWidth = canvas.parentElement?.clientWidth || 600
    const maxHeight = window.innerHeight - 200
    const scale = Math.min(maxWidth / image.width, maxHeight / image.height)

    canvas.width = image.width * scale
    canvas.height = image.height * scale

    const ctx = canvas.getContext("2d")
    if (!ctx) return

    // Draw image
    ctx.drawImage(image, 0, 0, canvas.width, canvas.height)

    // Draw points and line
    if (points.length > 0) {
      // First point
      ctx.fillStyle = "#ef4444"
      ctx.beginPath()
      ctx.arc(points[0].x, points[0].y, 6, 0, Math.PI * 2)
      ctx.fill()

      if (points.length === 2) {
        // Second point
        ctx.fillStyle = "#3b82f6"
        ctx.beginPath()
        ctx.arc(points[1].x, points[1].y, 6, 0, Math.PI * 2)
        ctx.fill()

        // Line between points
        ctx.strokeStyle = "#6b7280"
        ctx.lineWidth = 2
        ctx.setLineDash([5, 5])
        ctx.beginPath()
        ctx.moveTo(points[0].x, points[0].y)
        ctx.lineTo(points[1].x, points[1].y)
        ctx.stroke()
        ctx.setLineDash([])

        // Distance text
        const dx = points[1].x - points[0].x
        const dy = points[1].y - points[0].y
        const distance = Math.sqrt(dx * dx + dy * dy)
        const midX = (points[0].x + points[1].x) / 2
        const midY = (points[0].y + points[1].y) / 2

        ctx.fillStyle = "#1f2937"
        ctx.font = "14px sans-serif"
        ctx.textAlign = "center"
        ctx.fillText(`${distance.toFixed(0)} px`, midX, midY - 10)
      }
    }
  }, [image, points])

  // Handle canvas click
  const handleCanvasClick = (e: React.MouseEvent<HTMLCanvasElement>) => {
    const canvas = canvasRef.current
    if (!canvas) return

    const rect = canvas.getBoundingClientRect()
    const scaleX = rect.width > 0 ? canvas.width / rect.width : 1
    const scaleY = rect.height > 0 ? canvas.height / rect.height : 1

    const x = (e.clientX - rect.left) * scaleX
    const y = (e.clientY - rect.top) * scaleY

    const newPoints = [...points, { x, y }]

    if (newPoints.length === 2) {
      // Calculate distance when we have two points
      const dx = newPoints[1].x - newPoints[0].x
      const dy = newPoints[1].y - newPoints[0].y
      const distance = Math.sqrt(dx * dx + dy * dy)
      onPointsSelectedAction(distance)
      setPoints(newPoints)
    } else if (newPoints.length > 2) {
      // Reset to single point
      setPoints([newPoints[newPoints.length - 1]])
    } else {
      setPoints(newPoints)
    }
  }

  const handleReset = () => {
    setPoints([])
  }

  return (
    <div className="flex flex-col gap-4 rounded-lg border border-gray-200 bg-white p-6 shadow-sm">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-lg font-semibold text-gray-900">Floor Plan</h2>
          <p className="mt-1 text-sm text-gray-600">Click two points to measure a known wall</p>
        </div>
        {points.length > 0 && (
          <button
            onClick={handleReset}
            className="inline-flex items-center gap-2 rounded-lg border border-gray-300 bg-white px-3 py-2 text-sm font-medium text-gray-700 transition-colors hover:bg-gray-50 active:bg-gray-100"
          >
            <RotateCcw className="h-4 w-4" />
            Reset
          </button>
        )}
      </div>

      <div className="overflow-hidden rounded-lg border border-gray-200 bg-gray-50">
        <canvas ref={canvasRef} onClick={handleCanvasClick} className="block w-full cursor-crosshair bg-gray-50" />
      </div>

      {points.length > 0 && (
        <div className="flex items-center gap-2 rounded-lg bg-blue-50 px-3 py-2">
          <div className="h-2 w-2 rounded-full bg-blue-500" />
          <p className="text-xs text-gray-700">
            {points.length === 1
              ? "Click a second point to complete the measurement"
              : "Measurement complete. Click again to start a new measurement"}
          </p>
        </div>
      )}
    </div>
  )
}
