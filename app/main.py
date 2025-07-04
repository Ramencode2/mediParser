# app/main.py

import os
import shutil
import time
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import JSONResponse
from app.ocr_utils import extract_text_from_image
from app.parser import parse_lab_tests

app = FastAPI()

UPLOAD_DIR = "temp_uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@app.post("/get-lab-tests")
async def get_lab_tests(file: UploadFile = File(...)):
    temp_file_path = None
    try:
        # Validate file type
        if not file.filename.lower().endswith(('.png', '.jpg', '.jpeg', '.tiff', '.bmp')):
            raise HTTPException(status_code=400, detail="Only image files are supported")
        
        # Create safe filename
        safe_filename = file.filename.replace('/', '_').replace('\\', '_')
        temp_file_path = os.path.join(UPLOAD_DIR, safe_filename)
        
        # Save uploaded file
        with open(temp_file_path, "wb") as f:
            shutil.copyfileobj(file.file, f)

        # Extract text with timing
        start_time = time.time()
        raw_text = extract_text_from_image(temp_file_path)
        ocr_time = time.time() - start_time
        
        if not raw_text.strip():
            return {
                "filename": file.filename, 
                "data": [], 
                "message": "No text could be extracted from the image",
                "ocr_processing_time": round(ocr_time, 2)
            }

        # Parse with timing
        parse_start = time.time()
        structured_data = parse_lab_tests(raw_text)
        parse_time = time.time() - parse_start
        
        return {
            "filename": file.filename, 
            "data": structured_data,
            "total_tests_found": len(structured_data),
            "ocr_processing_time": round(ocr_time, 2),
            "parsing_time": round(parse_time, 2),
            "total_processing_time": round(ocr_time + parse_time, 2),
            "raw_text_preview": raw_text[:200] + "..." if len(raw_text) > 200 else raw_text
        }

    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except Exception as e:
        print(f"[ERROR] Processing file {file.filename}: {str(e)}")
        return JSONResponse(
            status_code=500, 
            content={
                "error": f"Internal server error: {str(e)}",
                "filename": file.filename
            }
        )
    finally:
        # Clean up temporary file
        if temp_file_path and os.path.exists(temp_file_path):
            try:
                os.remove(temp_file_path)
            except Exception as e:
                print(f"[WARNING] Could not remove temporary file {temp_file_path}: {e}")

@app.get("/health")
async def health_check():
    return {"status": "healthy", "message": "Lab test extractor is running"}

@app.get("/")
async def root():
    return {
        "message": "Lab Test Extractor API",
        "version": "2.0",
        "endpoints": {
            "POST /get-lab-tests": "Extract lab test results from image",
            "GET /health": "Health check",
            "GET /": "API information"
        }
    }
