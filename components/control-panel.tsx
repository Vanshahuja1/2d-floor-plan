"use client"

import type React from "react"

import { useState } from "react"
import { Upload } from "lucide-react"

interface ControlPanelProps {
  onImageUpload: (imageData: string) => void
  onWallLengthChange: (length: number) => void
  wallLengthMeters: number | null
  pixelDistance: number | null
  scale: number | null
}

export default function ControlPanel({
  onImageUpload,
  onWallLengthChange,
  wallLengthMeters,
  pixelDistance,
  scale,
}: ControlPanelProps) {
  const [inputValue, setInputValue] = useState<string>("")
  const [unit, setUnit] = useState<"m" | "cm" | "ft">("m")

  const toMeters = (value: number, selectedUnit: "m" | "cm" | "ft") => {
    if (selectedUnit === "cm") return value / 100
    if (selectedUnit === "ft") return value * 0.3048
    return value
  }

  const handleFileUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (file) {
      const reader = new FileReader()
      reader.onload = (event) => {
        const imageData = event.target?.result as string
        onImageUpload(imageData)
      }
      reader.readAsDataURL(file)
    }
  }

  const handleWallLengthChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const value = e.target.value
    setInputValue(value)
    const numValue = Number.parseFloat(value)
    if (!isNaN(numValue) && numValue > 0) {
      onWallLengthChange(toMeters(numValue, unit))
    }
  }

  const handleUnitChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    const nextUnit = e.target.value as "m" | "cm" | "ft"
    setUnit(nextUnit)

    const numValue = Number.parseFloat(inputValue)
    if (!isNaN(numValue) && numValue > 0) {
      onWallLengthChange(toMeters(numValue, nextUnit))
    }
  }

  return (
    <div className="flex flex-col gap-6 rounded-lg border border-gray-200 bg-white p-6 shadow-sm">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-semibold text-gray-900">Blueprint Calibration</h1>
        <p className="mt-2 text-sm text-gray-600">Set real-world scale from a known wall</p>
      </div>

      {/* Image Upload */}
      <div className="flex flex-col gap-3">
        <label className="text-sm font-medium text-gray-700">Floor Plan Image</label>
        <label className="flex cursor-pointer items-center gap-2 rounded-lg border-2 border-dashed border-gray-300 bg-gray-50 px-4 py-8 transition-colors hover:border-gray-400 hover:bg-gray-100">
          <Upload className="h-5 w-5 text-gray-500" />
          <span className="text-sm font-medium text-gray-700">Click to upload PNG or JPG</span>
          <input type="file" accept="image/png,image/jpeg" onChange={handleFileUpload} className="hidden" />
        </label>
      </div>

      {/* Wall Length Input */}
      <div className="flex flex-col gap-3">
        <label htmlFor="wall-length" className="text-sm font-medium text-gray-700">
          Known Wall Length
        </label>
        <div className="flex items-center gap-2">
          <input
            id="wall-length"
            type="number"
            min="0"
            step="0.1"
            value={inputValue}
            onChange={handleWallLengthChange}
            placeholder="Enter length"
            className="flex-1 rounded-lg border border-gray-300 bg-white px-3 py-2 text-sm text-gray-900 placeholder-gray-400 outline-none transition-colors focus:border-gray-400 focus:ring-1 focus:ring-gray-300"
          />
          <select
            value={unit}
            onChange={handleUnitChange}
            className="rounded-lg border border-gray-300 bg-white px-3 py-2 text-sm text-gray-900 outline-none transition-colors focus:border-gray-400 focus:ring-1 focus:ring-gray-300"
          >
            <option value="m">m</option>
            <option value="cm">cm</option>
            <option value="ft">ft</option>
          </select>
        </div>
      </div>

      {/* Divider */}
      <div className="border-t border-gray-200" />

      {/* Output Values */}
      <div className="flex flex-col gap-4">
        <h3 className="text-sm font-medium text-gray-700">Results</h3>

        {/* Pixel Distance */}
        <div className="rounded-lg bg-gray-50 p-3">
          <p className="text-xs text-gray-600">Pixel Length</p>
          <p className="mt-1 text-lg font-semibold text-gray-900">
            {pixelDistance ? pixelDistance.toFixed(2) : "—"} px
          </p>
        </div>

        {/* Scale */}
        <div className="rounded-lg bg-gray-50 p-3">
          <p className="text-xs text-gray-600">Scale Factor</p>
          <p className="mt-1 text-lg font-semibold text-gray-900">{scale ? scale.toFixed(4) : "—"} m/px</p>
        </div>

        {/* Status */}
        <div className="flex items-center gap-2 rounded-lg bg-blue-50 px-3 py-2">
          <div
            className={`h-2 w-2 rounded-full ${pixelDistance && wallLengthMeters ? "bg-green-500" : "bg-gray-300"}`}
          />
          <p className="text-xs text-gray-700">
            {pixelDistance && wallLengthMeters ? "Calibration complete" : "Select two points and enter wall length"}
          </p>
        </div>
      </div>

      {/* Instructions */}
      <div className="rounded-lg bg-gray-50 p-3">
        <p className="text-xs font-medium text-gray-700">Instructions</p>
        <ul className="mt-2 flex flex-col gap-1 text-xs text-gray-600">
          <li>1. Upload a floor plan image</li>
          <li>2. Click two points on the image to mark a known wall</li>
          <li>3. Enter the real-world wall length and select its unit</li>
          <li>4. Scale factor will be calculated automatically</li>
        </ul>
      </div>
    </div>
  )
}
