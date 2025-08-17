import { type NextRequest, NextResponse } from "next/server"

const BACKEND_URL = process.env.BACKEND_URL || "http://localhost:8000"

export async function GET(request: NextRequest, { params }: { params: { filename: string } }) {
  try {
    const { filename } = params

    // Get the PDF from the FastAPI backend
    const backendResponse = await fetch(`${BACKEND_URL}/download-pdf/${filename}`)

    if (!backendResponse.ok) {
      return NextResponse.json(
        { is_success: false, error: "Failed to fetch PDF" },
        { status: backendResponse.status }
      )
    }

    // Get the PDF content as a blob
    const pdfBlob = await backendResponse.blob()

    // Return the PDF with proper headers
    return new NextResponse(pdfBlob, {
      headers: {
        "Content-Type": "application/pdf",
        "Content-Disposition": `inline; filename="${filename}"`,
      },
    })
  } catch (error) {
    console.error("Error downloading PDF:", error)
    return NextResponse.json(
      { is_success: false, error: "Server error downloading PDF" },
      { status: 500 }
    )
  }
}
