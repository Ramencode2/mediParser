import { type NextRequest, NextResponse } from "next/server"

const BACKEND_URL = process.env.BACKEND_URL || "http://localhost:8000"

export async function POST(request: NextRequest) {
  try {
    const formData = await request.formData()
    const file = formData.get("file") as File
    const patientName = formData.get("patient_name") as string

    if (!file || !patientName) {
      return NextResponse.json(
        { is_success: false, error: "Missing file or patient name" },
        { status: 400 }
      )
    }

    // Forward request to FastAPI backend
    const backendResponse = await fetch(`${BACKEND_URL}/extract-lab-tests`, {
      method: "POST",
      body: formData, // Forward the same formData received from the client
    })

    if (!backendResponse.ok) {
      const error = await backendResponse.json()
      return NextResponse.json(
        { is_success: false, error: error.detail || "Failed to process lab report" },
        { status: backendResponse.status }
      )
    }

    const data = await backendResponse.json()
    return NextResponse.json(data)
  } catch (error) {
    console.error("Error processing request:", error)
    return NextResponse.json(
      { is_success: false, error: "Server error processing request" },
      { status: 500 }
    )
  }
}
