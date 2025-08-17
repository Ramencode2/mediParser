"use client"

import { useState } from "react"
import { Button } from "@/components/ui/button"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
  DropdownMenuSeparator,
  DropdownMenuLabel,
} from "@/components/ui/dropdown-menu"
import { Share, Mail, MessageSquare, Smartphone, Copy, Download, Check } from "lucide-react"

interface EnhancedShareProps {
  pdfPath: string
  patientName?: string
}

export function EnhancedShare({ pdfPath, patientName }: EnhancedShareProps) {
  const [isSharing, setIsSharing] = useState(false)
  const [copied, setCopied] = useState(false)

  const shareTitle = `Lab Report - ${patientName || "Patient"}`
  const shareText = `Medical lab report analysis results for ${patientName || "patient"}`

  const handleNativeShare = async () => {
    setIsSharing(true)
    try {
      // Fetch the PDF from the API
      const response = await fetch(`/api/download-pdf/${encodeURIComponent(pdfPath)}`)
      if (!response.ok) throw new Error("Failed to fetch PDF")

      const blob = await response.blob()
      const file = new File([blob], `lab-report-${patientName}-${new Date().toISOString()}.pdf`, { 
        type: "application/pdf" 
      })

      if (navigator.share && navigator.canShare && navigator.canShare({ files: [file] })) {
        await navigator.share({
          title: shareTitle,
          text: shareText,
          files: [file],
        })
      } else if (navigator.share) {
        await navigator.share({
          title: shareTitle,
          text: shareText,
          url: window.location.href,
        })
      } else {
        throw new Error("Native sharing not supported")
      }
    } catch (error) {
      console.error("Native share failed:", error)
      // Fallback to download
      handleDownloadShare()
    } finally {
      setIsSharing(false)
    }
  }

  const handleDownloadShare = async () => {
    try {
      const response = await fetch(`/api/download-pdf/${encodeURIComponent(pdfPath)}`)
      const blob = await response.blob()
      const url = URL.createObjectURL(blob)
      const link = document.createElement("a")
      link.href = url
      link.download = `lab-report-${patientName}-${new Date().toISOString()}.pdf`
      link.click()
      URL.revokeObjectURL(url)
    } catch (error) {
      console.error("Download failed:", error)
    }
  }

  const handleEmailShare = () => {
    const subject = encodeURIComponent(shareTitle)
    const body = encodeURIComponent(`${shareText}\n\nView report: ${window.location.href}`)
    window.open(`mailto:?subject=${subject}&body=${body}`)
  }

  const handleSMSShare = () => {
    const text = encodeURIComponent(`${shareText}\nView report: ${window.location.href}`)
    window.open(`sms:?body=${text}`)
  }

  const handleWhatsAppShare = () => {
    const text = encodeURIComponent(`${shareText}\nView report: ${window.location.href}`)
    window.open(`https://wa.me/?text=${text}`)
  }

  const handleCopyLink = async () => {
    try {
      await navigator.clipboard.writeText(window.location.href)
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    } catch (error) {
      console.error("Copy failed:", error)
    }
  }

  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button
          variant="outline"
          size="sm"
          disabled={isSharing}
          className="bg-white hover:bg-orange-50 border-orange-200 text-orange-700 hover:text-orange-800 shadow-sm hover:shadow-md transition-all duration-200 disabled:opacity-50"
        >
          {isSharing ? (
            <div className="animate-spin rounded-full h-4 w-4 border-2 border-orange-500 border-t-transparent mr-2"></div>
          ) : (
            <Share className="h-4 w-4 mr-2" />
          )}
          {isSharing ? "Sharing..." : "Share"}
        </Button>
      </DropdownMenuTrigger>

      <DropdownMenuContent className="w-56 bg-white/95 backdrop-blur-sm border-orange-200 shadow-xl">
        <DropdownMenuLabel className="text-orange-800 font-semibold">Share Lab Report</DropdownMenuLabel>
        <DropdownMenuSeparator className="bg-orange-100" />

        {/* Native Share (Mobile Apps) */}
        <DropdownMenuItem onClick={handleNativeShare} className="hover:bg-orange-50 cursor-pointer">
          <Smartphone className="h-4 w-4 mr-3 text-blue-600" />
          <div>
            <div className="font-medium">Share to Apps</div>
            <div className="text-xs text-gray-500">WhatsApp, Telegram, etc.</div>
          </div>
        </DropdownMenuItem>

        <DropdownMenuSeparator className="bg-gray-100" />

        {/* Email */}
        <DropdownMenuItem onClick={handleEmailShare} className="hover:bg-blue-50 cursor-pointer">
          <Mail className="h-4 w-4 mr-3 text-blue-600" />
          <div>
            <div className="font-medium">Email</div>
            <div className="text-xs text-gray-500">Send via email client</div>
          </div>
        </DropdownMenuItem>

        {/* SMS */}
        <DropdownMenuItem onClick={handleSMSShare} className="hover:bg-green-50 cursor-pointer">
          <MessageSquare className="h-4 w-4 mr-3 text-green-600" />
          <div>
            <div className="font-medium">Text Message</div>
            <div className="text-xs text-gray-500">Send via SMS</div>
          </div>
        </DropdownMenuItem>

        {/* WhatsApp */}
        <DropdownMenuItem onClick={handleWhatsAppShare} className="hover:bg-green-50 cursor-pointer">
          <MessageSquare className="h-4 w-4 mr-3 text-green-600" />
          <div>
            <div className="font-medium">WhatsApp</div>
            <div className="text-xs text-gray-500">Share via WhatsApp Web</div>
          </div>
        </DropdownMenuItem>

        <DropdownMenuSeparator className="bg-gray-100" />

        {/* Copy Link */}
        <DropdownMenuItem onClick={handleCopyLink} className="hover:bg-purple-50 cursor-pointer">
          {copied ? (
            <Check className="h-4 w-4 mr-3 text-green-600" />
          ) : (
            <Copy className="h-4 w-4 mr-3 text-purple-600" />
          )}
          <div>
            <div className="font-medium">{copied ? "Link Copied!" : "Copy Link"}</div>
            <div className="text-xs text-gray-500">Copy report URL</div>
          </div>
        </DropdownMenuItem>

        {/* Download & Share */}
        <DropdownMenuItem onClick={handleDownloadShare} className="hover:bg-indigo-50 cursor-pointer">
          <Download className="h-4 w-4 mr-3 text-indigo-600" />
          <div>
            <div className="font-medium">Download PDF</div>
            <div className="text-xs text-gray-500">Save to device</div>
          </div>
        </DropdownMenuItem>
      </DropdownMenuContent>
    </DropdownMenu>
  )
}
