"use client"

import { useState } from "react"
import { Button } from "@/components/ui/button"
import { ZoomIn, ZoomOut, RotateCw, Download } from "lucide-react"

interface ImagePreviewProps {
  image: File
}

export function ImagePreview({ image }: ImagePreviewProps) {
  const [zoom, setZoom] = useState(1)
  const [rotation, setRotation] = useState(0)
  const imageUrl = URL.createObjectURL(image)

  const handleZoomIn = () => setZoom((prev) => Math.min(prev + 0.25, 3))
  const handleZoomOut = () => setZoom((prev) => Math.max(prev - 0.25, 0.5))
  const handleRotate = () => setRotation((prev) => (prev + 90) % 360)

  const handleDownload = () => {
    const link = document.createElement("a")
    link.href = imageUrl
    link.download = image.name
    link.click()
  }

  return (
    <div className="space-y-6">
      {/* Enhanced Controls */}
      <div className="flex items-center justify-between bg-gradient-to-r from-gray-50 to-blue-50 rounded-xl p-4 border border-gray-200">
        <div className="flex items-center gap-3">
          <div className="flex items-center bg-white rounded-lg border border-gray-200 shadow-sm">
            <Button
              variant="ghost"
              size="sm"
              onClick={handleZoomOut}
              disabled={zoom <= 0.5}
              className="hover:bg-blue-50 disabled:opacity-50"
            >
              <ZoomOut className="h-4 w-4" />
            </Button>
            <div className="px-4 py-2 bg-gradient-to-r from-blue-500 to-indigo-500 text-white font-bold text-sm min-w-[70px] text-center">
              {Math.round(zoom * 100)}%
            </div>
            <Button
              variant="ghost"
              size="sm"
              onClick={handleZoomIn}
              disabled={zoom >= 3}
              className="hover:bg-blue-50 disabled:opacity-50"
            >
              <ZoomIn className="h-4 w-4" />
            </Button>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={handleRotate}
            className="bg-white hover:bg-blue-50 border-gray-200 shadow-sm"
          >
            <RotateCw className="h-4 w-4 mr-2" />
            Rotate
          </Button>
          <Button
            variant="outline"
            size="sm"
            onClick={handleDownload}
            className="bg-white hover:bg-green-50 border-gray-200 shadow-sm text-green-700 hover:text-green-800"
          >
            <Download className="h-4 w-4 mr-2" />
            Download
          </Button>
        </div>
      </div>

      {/* Enhanced Image Container */}
      <div className="relative border-2 border-gray-200 rounded-2xl overflow-hidden bg-gradient-to-br from-gray-50 to-blue-50 shadow-inner">
        {/* Corner decorations */}
        <div className="absolute top-0 left-0 w-8 h-8 border-t-4 border-l-4 border-blue-500 rounded-tl-2xl"></div>
        <div className="absolute top-0 right-0 w-8 h-8 border-t-4 border-r-4 border-blue-500 rounded-tr-2xl"></div>
        <div className="absolute bottom-0 left-0 w-8 h-8 border-b-4 border-l-4 border-blue-500 rounded-bl-2xl"></div>
        <div className="absolute bottom-0 right-0 w-8 h-8 border-b-4 border-r-4 border-blue-500 rounded-br-2xl"></div>

        <div className="overflow-auto max-h-[600px] scrollbar-thin scrollbar-thumb-blue-300 scrollbar-track-gray-100">
          <div className="flex items-center justify-center min-h-[400px] p-6">
            <div className="relative">
              {/* Image shadow */}
              <div className="absolute inset-0 bg-black/10 rounded-lg blur-lg transform translate-x-2 translate-y-2"></div>
              <img
                src={imageUrl || "/placeholder.svg"}
                alt="Lab report preview"
                className="relative max-w-full h-auto transition-transform duration-300 rounded-lg shadow-lg"
                style={{
                  transform: `scale(${zoom}) rotate(${rotation}deg)`,
                  transformOrigin: "center",
                }}
              />
            </div>
          </div>
        </div>
      </div>

      {/* Enhanced Image Info */}
      <div className="bg-gradient-to-r from-white to-gray-50 rounded-xl p-6 border border-gray-200 shadow-sm">
        <h3 className="font-semibold text-gray-900 mb-4 flex items-center gap-2">
          <div className="w-2 h-2 bg-blue-500 rounded-full"></div>
          File Information
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="space-y-1">
            <span className="text-sm text-gray-500 font-medium">File name</span>
            <p className="font-semibold text-gray-900 truncate">{image.name}</p>
          </div>
          <div className="space-y-1">
            <span className="text-sm text-gray-500 font-medium">File size</span>
            <p className="font-semibold text-gray-900">{(image.size / 1024 / 1024).toFixed(2)} MB</p>
          </div>
          <div className="space-y-1">
            <span className="text-sm text-gray-500 font-medium">File type</span>
            <div className="flex items-center gap-2">
              <div className="w-3 h-3 bg-green-500 rounded-full"></div>
              <p className="font-semibold text-gray-900">{image.type.split("/")[1].toUpperCase()}</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
