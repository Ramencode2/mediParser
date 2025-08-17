"use client"

import { useState } from "react"
import { UploadSection } from "@/components/upload-section"
import { ImagePreview } from "@/components/image-preview"
import { ResultsTable } from "@/components/results-table"
import { PDFActions } from "@/components/pdf-actions"
import { Separator } from "@/components/ui/separator"
import { FileText, Activity } from "lucide-react"

export interface LabResult {
  test_name: string
  test_value: string
  bio_reference_range: string
  test_unit: string
  lab_test_out_of_range: boolean
}

export default function LabReportViewer() {
  const [uploadedImage, setUploadedImage] = useState<File | null>(null)
  const [patientName, setPatientName] = useState("")
  const [results, setResults] = useState<LabResult[]>([])
  const [pdfPath, setPdfPath] = useState<string | null>(null)
  const [isProcessing, setIsProcessing] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const handleUpload = async (file: File, patient: string) => {
    setIsProcessing(true)
    setError(null)

    try {
      const formData = new FormData()
      formData.append("file", file)
      formData.append("patient_name", patient)

      const response = await fetch("/api/extract-lab-tests", {
        method: "POST",
        body: formData,
      })

      const data = await response.json()

      if (data.is_success) {
        setResults(data.data)
        setPdfPath(data.pdf_path)
        setUploadedImage(file)
        setPatientName(patient)
      } else {
        setError("Failed to process lab report. Please try again.")
      }
    } catch (err) {
      setError("Network error. Please check your connection and try again.")
    } finally {
      setIsProcessing(false)
    }
  }

  const handleReset = () => {
    setUploadedImage(null)
    setPatientName("")
    setResults([])
    setPdfPath(null)
    setError(null)
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-indigo-50 to-purple-50">
      {/* Background Pattern */}
      <div className="absolute inset-0 bg-grid-pattern opacity-5"></div>

      <div className="relative container mx-auto p-4 space-y-8">
        {/* Enhanced Header */}
        <div className="text-center space-y-4 py-8">
          <div className="flex items-center justify-center gap-3 mb-6">
            <div className="relative">
              <div className="absolute inset-0 bg-blue-600 rounded-xl blur-lg opacity-30"></div>
              <div className="relative p-3 bg-gradient-to-br from-blue-600 to-blue-700 rounded-xl shadow-lg">
                <Activity className="h-8 w-8 text-white" />
              </div>
            </div>
            <div>
              <h1 className="text-4xl font-bold bg-gradient-to-r from-blue-900 via-blue-700 to-indigo-600 bg-clip-text text-transparent">
                Medical Lab Report Viewer
              </h1>
              <div className="h-1 w-32 bg-gradient-to-r from-blue-500 to-indigo-500 rounded-full mx-auto mt-2"></div>
            </div>
          </div>
          <p className="text-gray-600 max-w-2xl mx-auto text-lg leading-relaxed">
            Upload lab report images to automatically extract and analyze test results. Generate professional PDF
            reports with color-coded status indicators for better medical insights.
          </p>

          {/* Feature Pills */}
          <div className="flex flex-wrap justify-center gap-3 mt-6">
            <div className="px-4 py-2 bg-white/70 backdrop-blur-sm rounded-full text-sm font-medium text-gray-700 border border-gray-200 shadow-sm">
              🔍 AI-Powered Analysis
            </div>
            <div className="px-4 py-2 bg-white/70 backdrop-blur-sm rounded-full text-sm font-medium text-gray-700 border border-gray-200 shadow-sm">
              📊 Color-Coded Results
            </div>
            <div className="px-4 py-2 bg-white/70 backdrop-blur-sm rounded-full text-sm font-medium text-gray-700 border border-gray-200 shadow-sm">
              📄 PDF Generation
            </div>
          </div>
        </div>

        {!uploadedImage ? (
          /* Enhanced Upload Interface */
          <div className="max-w-3xl mx-auto">
            <div className="bg-white/80 backdrop-blur-sm rounded-2xl shadow-xl border border-white/20 p-8 relative overflow-hidden">
              {/* Decorative Elements */}
              <div className="absolute top-0 right-0 w-32 h-32 bg-gradient-to-br from-blue-100 to-indigo-100 rounded-full -translate-y-16 translate-x-16 opacity-50"></div>
              <div className="absolute bottom-0 left-0 w-24 h-24 bg-gradient-to-tr from-purple-100 to-pink-100 rounded-full translate-y-12 -translate-x-12 opacity-50"></div>

              <div className="relative">
                <UploadSection onUpload={handleUpload} isProcessing={isProcessing} error={error} />
              </div>
            </div>
          </div>
        ) : (
          /* Enhanced Two-Panel View */
          <div className="grid lg:grid-cols-2 gap-8">
            {/* Left Panel - Enhanced Image Preview */}
            <div className="space-y-6">
              <div className="bg-white/80 backdrop-blur-sm rounded-2xl shadow-xl border border-white/20 p-6 relative overflow-hidden">
                {/* Decorative gradient */}
                <div className="absolute top-0 left-0 right-0 h-1 bg-gradient-to-r from-blue-500 via-indigo-500 to-purple-500"></div>

                <div className="space-y-6">
                  <div className="flex items-center justify-between">
                    <h2 className="text-2xl font-bold flex items-center gap-3 text-gray-900">
                      <div className="p-2 bg-gradient-to-br from-blue-100 to-indigo-100 rounded-lg">
                        <FileText className="h-6 w-6 text-blue-600" />
                      </div>
                      Lab Report Image
                    </h2>
                    <button
                      onClick={handleReset}
                      className="px-4 py-2 text-sm bg-gradient-to-r from-blue-500 to-indigo-500 text-white rounded-lg hover:from-blue-600 hover:to-indigo-600 transition-all duration-200 shadow-md hover:shadow-lg transform hover:-translate-y-0.5"
                    >
                      Upload New Report
                    </button>
                  </div>

                  {/* Enhanced Patient Info */}
                  <div className="bg-gradient-to-r from-blue-50 to-indigo-50 rounded-xl p-4 border border-blue-100">
                    <div className="flex items-center gap-3">
                      <div className="w-10 h-10 bg-gradient-to-br from-blue-500 to-indigo-500 rounded-full flex items-center justify-center text-white font-semibold text-sm">
                        {patientName.charAt(0).toUpperCase()}
                      </div>
                      <div>
                        <p className="text-sm text-gray-600 font-medium">Patient Name</p>
                        <p className="font-semibold text-gray-900">{patientName}</p>
                      </div>
                    </div>
                  </div>

                  <ImagePreview image={uploadedImage} />
                </div>
              </div>
            </div>

            {/* Right Panel - Enhanced Results */}
            <div className="space-y-6">
              <div className="bg-white/80 backdrop-blur-sm rounded-2xl shadow-xl border border-white/20 p-6 relative overflow-hidden">
                {/* Decorative gradient */}
                <div className="absolute top-0 left-0 right-0 h-1 bg-gradient-to-r from-green-500 via-blue-500 to-purple-500"></div>

                <div className="space-y-6">
                  <div className="flex items-center justify-between">
                    <h2 className="text-2xl font-bold flex items-center gap-3 text-gray-900">
                      <div className="p-2 bg-gradient-to-br from-green-100 to-emerald-100 rounded-lg">
                        <Activity className="h-6 w-6 text-green-600" />
                      </div>
                      Test Results
                    </h2>
                    {pdfPath && <PDFActions pdfPath={pdfPath} patientName={patientName} />}
                  </div>

                  <Separator className="bg-gradient-to-r from-transparent via-gray-200 to-transparent" />

                  {isProcessing ? (
                    <div className="flex items-center justify-center py-16">
                      <div className="text-center space-y-6">
                        <div className="relative">
                          <div className="animate-spin rounded-full h-16 w-16 border-4 border-blue-100 border-t-blue-500 mx-auto"></div>
                          <div className="absolute inset-0 rounded-full bg-gradient-to-r from-blue-400 to-indigo-400 opacity-20 animate-pulse"></div>
                        </div>
                        <div className="space-y-2">
                          <p className="text-lg font-semibold text-gray-900">Processing lab report...</p>
                          <p className="text-sm text-gray-600">Analyzing test results with AI</p>
                        </div>
                        <div className="flex justify-center space-x-1">
                          <div className="w-2 h-2 bg-blue-500 rounded-full animate-bounce"></div>
                          <div
                            className="w-2 h-2 bg-blue-500 rounded-full animate-bounce"
                            style={{ animationDelay: "0.1s" }}
                          ></div>
                          <div
                            className="w-2 h-2 bg-blue-500 rounded-full animate-bounce"
                            style={{ animationDelay: "0.2s" }}
                          ></div>
                        </div>
                      </div>
                    </div>
                  ) : (
                    <ResultsTable data={results} />
                  )}
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
