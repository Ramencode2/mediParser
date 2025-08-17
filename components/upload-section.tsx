"use client"

import { useState, useCallback } from "react"
import { useDropzone } from "react-dropzone"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Alert, AlertDescription } from "@/components/ui/alert"
import { Progress } from "@/components/ui/progress"
import { Upload, FileImage, AlertCircle, Activity } from "lucide-react"

interface UploadSectionProps {
  onUpload: (file: File, patientName: string) => Promise<void>
  isProcessing: boolean
  error: string | null
}

export function UploadSection({ onUpload, isProcessing, error }: UploadSectionProps) {
  const [selectedFile, setSelectedFile] = useState<File | null>(null)
  const [patientName, setPatientName] = useState("")
  const [uploadProgress, setUploadProgress] = useState(0)

  const onDrop = useCallback((acceptedFiles: File[]) => {
    if (acceptedFiles.length > 0) {
      setSelectedFile(acceptedFiles[0])
    }
  }, [])

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      "image/*": [".jpg", ".jpeg", ".png"],
    },
    multiple: false,
    disabled: isProcessing,
  })

  const handleUpload = async () => {
    if (!selectedFile || !patientName.trim()) return

    // Simulate upload progress
    setUploadProgress(0)
    const progressInterval = setInterval(() => {
      setUploadProgress((prev) => {
        if (prev >= 90) {
          clearInterval(progressInterval)
          return 90
        }
        return prev + 10
      })
    }, 200)

    try {
      await onUpload(selectedFile, patientName.trim())
      setUploadProgress(100)
    } finally {
      clearInterval(progressInterval)
      setTimeout(() => setUploadProgress(0), 1000)
    }
  }

  const isValid = selectedFile && patientName.trim() && !isProcessing

  return (
    <div className="space-y-8">
      <div className="text-center space-y-3">
        <h2 className="text-3xl font-bold bg-gradient-to-r from-gray-900 to-gray-700 bg-clip-text text-transparent">
          Upload Lab Report
        </h2>
        <p className="text-gray-600 text-lg">Drag and drop your lab report image or click to browse</p>
      </div>

      {/* Enhanced Drag and Drop Zone */}
      <div
        {...getRootProps()}
        className={`
        relative border-2 border-dashed rounded-2xl p-12 text-center cursor-pointer transition-all duration-300 group
        ${
          isDragActive
            ? "border-blue-400 bg-gradient-to-br from-blue-50 to-indigo-50 scale-105 shadow-lg"
            : "border-gray-300 hover:border-blue-300 hover:bg-gradient-to-br hover:from-gray-50 hover:to-blue-50"
        }
        ${isProcessing ? "opacity-50 cursor-not-allowed" : "hover:shadow-xl"}
      `}
      >
        {/* Background decoration */}
        <div className="absolute inset-0 bg-gradient-to-br from-blue-500/5 to-indigo-500/5 rounded-2xl opacity-0 group-hover:opacity-100 transition-opacity duration-300"></div>

        <input {...getInputProps()} />
        <div className="relative space-y-6">
          {selectedFile ? (
            <div className="space-y-4">
              <div className="flex items-center justify-center">
                <div className="relative">
                  <div className="absolute inset-0 bg-green-500 rounded-full blur-lg opacity-30 animate-pulse"></div>
                  <div className="relative p-4 bg-gradient-to-br from-green-500 to-emerald-500 rounded-full">
                    <FileImage className="h-12 w-12 text-white" />
                  </div>
                </div>
              </div>
              <div className="bg-white/80 backdrop-blur-sm rounded-xl p-4 border border-green-200 shadow-sm">
                <div className="flex items-center justify-center gap-4">
                  <div className="text-left">
                    <p className="font-semibold text-green-700 text-lg">{selectedFile.name}</p>
                    <p className="text-sm text-gray-600">
                      {(selectedFile.size / 1024 / 1024).toFixed(2)} MB • Ready to upload
                    </p>
                  </div>
                  <div className="w-8 h-8 bg-green-100 rounded-full flex items-center justify-center">
                    <div className="w-3 h-3 bg-green-500 rounded-full"></div>
                  </div>
                </div>
              </div>
            </div>
          ) : (
            <div className="space-y-6">
              <div className="relative">
                <div className="absolute inset-0 bg-blue-500 rounded-full blur-xl opacity-20 animate-pulse"></div>
                <div className="relative p-6 bg-gradient-to-br from-blue-500 to-indigo-500 rounded-full mx-auto w-fit">
                  <Upload className="h-16 w-16 text-white" />
                </div>
              </div>
              <div className="space-y-2">
                <p className="text-2xl font-semibold text-gray-900">
                  {isDragActive ? "Drop the file here" : "Choose lab report image"}
                </p>
                <p className="text-gray-500">Supports JPG, PNG formats up to 10MB</p>
              </div>

              {/* File format indicators */}
              <div className="flex justify-center gap-4 pt-4">
                <div className="flex items-center gap-2 px-3 py-2 bg-white/60 rounded-lg border border-gray-200">
                  <div className="w-3 h-3 bg-blue-500 rounded-full"></div>
                  <span className="text-sm font-medium text-gray-700">JPG</span>
                </div>
                <div className="flex items-center gap-2 px-3 py-2 bg-white/60 rounded-lg border border-gray-200">
                  <div className="w-3 h-3 bg-green-500 rounded-full"></div>
                  <span className="text-sm font-medium text-gray-700">PNG</span>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Enhanced Patient Name Input */}
      <div className="space-y-3">
        <Label htmlFor="patient-name" className="text-lg font-semibold text-gray-900 flex items-center gap-2">
          <div className="w-2 h-2 bg-red-500 rounded-full"></div>
          Patient Name
        </Label>
        <div className="relative">
          <Input
            id="patient-name"
            type="text"
            placeholder="Enter patient's full name"
            value={patientName}
            onChange={(e) => setPatientName(e.target.value)}
            disabled={isProcessing}
            className="text-lg py-4 px-6 rounded-xl border-2 border-gray-200 focus:border-blue-500 focus:ring-4 focus:ring-blue-100 transition-all duration-200 bg-white/80 backdrop-blur-sm"
          />
          <div className="absolute right-4 top-1/2 transform -translate-y-1/2">
            <div
              className={`w-3 h-3 rounded-full transition-colors duration-200 ${
                patientName.trim() ? "bg-green-500" : "bg-gray-300"
              }`}
            ></div>
          </div>
        </div>
      </div>

      {/* Enhanced Upload Progress */}
      {isProcessing && uploadProgress > 0 && (
        <div className="space-y-4 bg-white/80 backdrop-blur-sm rounded-xl p-6 border border-blue-200">
          <div className="flex justify-between items-center">
            <span className="font-semibold text-gray-900">Processing Report...</span>
            <span className="text-blue-600 font-bold">{uploadProgress}%</span>
          </div>
          <div className="relative">
            <Progress value={uploadProgress} className="h-3 bg-gray-200" />
            <div className="absolute inset-0 bg-gradient-to-r from-blue-500 to-indigo-500 rounded-full opacity-20 animate-pulse"></div>
          </div>
          <div className="flex items-center gap-2 text-sm text-gray-600">
            <div className="animate-spin rounded-full h-4 w-4 border-2 border-blue-500 border-t-transparent"></div>
            Analyzing medical data with AI...
          </div>
        </div>
      )}

      {/* Enhanced Error Message */}
      {error && (
        <div className="relative">
          <Alert variant="destructive" className="border-red-200 bg-red-50/80 backdrop-blur-sm rounded-xl">
            <div className="absolute top-0 left-0 right-0 h-1 bg-gradient-to-r from-red-500 to-pink-500 rounded-t-xl"></div>
            <AlertCircle className="h-5 w-5" />
            <AlertDescription className="text-red-800 font-medium">{error}</AlertDescription>
          </Alert>
        </div>
      )}

      {/* Enhanced Upload Button */}
      <div className="relative">
        <Button
          onClick={handleUpload}
          disabled={!isValid}
          className={`
          w-full text-lg py-6 rounded-xl font-semibold transition-all duration-300 transform
          ${
            isValid
              ? "bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-700 hover:to-indigo-700 shadow-lg hover:shadow-xl hover:-translate-y-1 text-white"
              : "bg-gray-300 text-gray-500 cursor-not-allowed"
          }
        `}
        >
          {isProcessing ? (
            <div className="flex items-center justify-center gap-3">
              <div className="animate-spin rounded-full h-6 w-6 border-2 border-white border-t-transparent"></div>
              <span>Processing Report...</span>
              <div className="flex space-x-1">
                <div className="w-1 h-1 bg-white rounded-full animate-bounce"></div>
                <div className="w-1 h-1 bg-white rounded-full animate-bounce" style={{ animationDelay: "0.1s" }}></div>
                <div className="w-1 h-1 bg-white rounded-full animate-bounce" style={{ animationDelay: "0.2s" }}></div>
              </div>
            </div>
          ) : (
            <div className="flex items-center justify-center gap-3">
              <Activity className="h-6 w-6" />
              <span>Analyze Lab Report</span>
            </div>
          )}
        </Button>

        {/* Button glow effect */}
        {isValid && !isProcessing && (
          <div className="absolute inset-0 bg-gradient-to-r from-blue-600 to-indigo-600 rounded-xl blur-lg opacity-30 -z-10 animate-pulse"></div>
        )}
      </div>

      <div className="text-center">
        <div className="text-sm text-gray-500 flex items-center justify-center gap-2">
          <span className="w-4 h-4 bg-green-500 rounded-full flex items-center justify-center">
            <span className="w-2 h-2 bg-white rounded-full"></span>
          </span>
          Your data is processed securely and not stored permanently
        </div>
      </div>
    </div>
  )
}
