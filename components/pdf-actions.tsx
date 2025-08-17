"use client"

import { useState } from "react"
import { Button } from "@/components/ui/button"
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog"
import { Download, Eye, Printer, FileText } from "lucide-react"
import { EnhancedShare } from "@/components/enhanced-share"

interface PDFActionsProps {
  pdfPath: string
  patientName?: string
}

export function PDFActions({ pdfPath, patientName }: PDFActionsProps) {
  const [isDownloading, setIsDownloading] = useState(false)
  const [showPreview, setShowPreview] = useState(false)

  const handleDownload = async () => {
    setIsDownloading(true)
    try {
      const response = await fetch(`/api/download-pdf/${pdfPath}`)
      if (response.ok) {
        const blob = await response.blob()
        const url = URL.createObjectURL(blob)
        const link = document.createElement("a")
        link.href = url
        link.download = `lab-report-${pdfPath}`
        link.click()
        URL.revokeObjectURL(url)
      }
    } catch (error) {
      console.error("Download failed:", error)
    } finally {
      setIsDownloading(false)
    }
  }

  const handlePrint = () => {
    window.print()
  }

  return (
    <div className="flex items-center gap-3">
      {/* Enhanced PDF Preview */}
      <Dialog open={showPreview} onOpenChange={setShowPreview}>
        <DialogTrigger asChild>
          <Button
            variant="outline"
            size="sm"
            className="bg-gradient-to-r from-blue-500 to-indigo-500 text-white border-0 hover:from-blue-600 hover:to-indigo-600 shadow-md hover:shadow-lg transition-all duration-200"
          >
            <Eye className="h-4 w-4 mr-2" />
            Preview
          </Button>
        </DialogTrigger>
        <DialogContent className="max-w-5xl max-h-[90vh] bg-white/95 backdrop-blur-sm">
          <DialogHeader>
            <DialogTitle className="text-2xl font-bold flex items-center gap-2">
              <div className="p-2 bg-gradient-to-br from-blue-500 to-indigo-500 rounded-lg">
                <FileText className="h-5 w-5 text-white" />
              </div>
              PDF Preview
            </DialogTitle>
          </DialogHeader>
          <div className="flex-1 overflow-auto rounded-xl border-2 border-gray-200 shadow-inner">
            <iframe src={`/api/download-pdf/${pdfPath}`} className="w-full h-[700px] rounded-xl" title="PDF Preview" />
          </div>
        </DialogContent>
      </Dialog>

      {/* Enhanced Download PDF */}
      <Button
        onClick={handleDownload}
        disabled={isDownloading}
        size="sm"
        className="bg-gradient-to-r from-green-500 to-emerald-500 text-white border-0 hover:from-green-600 hover:to-emerald-600 shadow-md hover:shadow-lg transition-all duration-200 disabled:opacity-50"
      >
        {isDownloading ? (
          <div className="animate-spin rounded-full h-4 w-4 border-2 border-white border-t-transparent mr-2"></div>
        ) : (
          <Download className="h-4 w-4 mr-2" />
        )}
        Download PDF
      </Button>

      {/* Enhanced Print */}
      <Button
        variant="outline"
        size="sm"
        onClick={handlePrint}
        className="bg-white hover:bg-purple-50 border-purple-200 text-purple-700 hover:text-purple-800 shadow-sm hover:shadow-md transition-all duration-200"
      >
        <Printer className="h-4 w-4 mr-2" />
        Print
      </Button>

      {/* Enhanced Share */}
      <EnhancedShare pdfPath={pdfPath} patientName={patientName} />
    </div>
  )
}
