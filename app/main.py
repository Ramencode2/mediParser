# app/main.py

import os
import time
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.responses import JSONResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from app.ocr_utils import (
    extract_text_with_easyocr,
    clean_ocr_text,
    parse_lab_test_line,
    extract_structured_lab_data,
    split_ocr_text_into_lines
)
from app.result_formatter import format_result, is_test_out_of_range
from app.parser import MedicalDocumentParser
from app.pdf_utils import create_lab_report_pdf, PDF_OUTPUT_DIR
from fastapi.exceptions import RequestValidationError
from starlette.requests import Request
from starlette.status import HTTP_422_UNPROCESSABLE_ENTITY
import cv2
import numpy as np
from ultralytics import YOLO
import logging
import torch

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Check CUDA availability
CUDA_AVAILABLE = torch.cuda.is_available()
if CUDA_AVAILABLE:
    logger.info(f"CUDA is available. Using GPU: {torch.cuda.get_device_name(0)}")
else:
    logger.info("CUDA is not available. Using CPU.")

app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # List of allowed origins (frontend URL)
    allow_credentials=True,
    allow_methods=["*"],  # Allow all methods
    allow_headers=["*"],  # Allow all headers
)

# Initialize both parsers
parser = MedicalDocumentParser()

# Load YOLO model
try:
    model = YOLO("C:/Users/Aditya/Desktop/lab_report_yolo_dataset/runs/detect/train3/weights/best.pt")
    if CUDA_AVAILABLE:
        model.to('cuda')  # Move model to GPU if available
    YOLO_AVAILABLE = True
    logger.info(f"YOLO model loaded successfully on {'GPU' if CUDA_AVAILABLE else 'CPU'}")
except Exception as e:
    YOLO_AVAILABLE = False
    logger.warning(f"Could not load YOLO model: {str(e)}")

CLASS_NAMES = ['Test_Name', 'Test_Value', 'Test_Unit', 'Flag', 'Ref_Range']

@app.post("/extract-lab-tests")
async def extract_lab_tests(
    file: UploadFile = File(...),
    patient_name: str = Form("Patient", description="Name of the patient for the PDF report")
):
    """Extract lab test results and generate both JSON and PDF reports."""
    logger.info(f"Received file: {file.filename}, Content-Type: {file.content_type}")
    
    if not file.content_type or not file.content_type.startswith("image/"):
        return JSONResponse(
            status_code=400,
            content={
                "is_success": False,
                "error": f"Uploaded file must be an image. Received content type: {file.content_type}"
            }
        )
    
    try:
        temp_path = f"_temp_{file.filename}"
        with open(temp_path, "wb") as f:
            f.write(await file.read())
            
        try:
            # Try YOLO-based extraction first if available
            if YOLO_AVAILABLE:
                try:
                    image = cv2.imread(temp_path)
                    results = model(image)[0]
                    structured_results = process_yolo_results(results, image)
                    if structured_results:
                        # Generate PDF report with automatic path generation
                        pdf_path = create_lab_report_pdf(structured_results, patient_name)
                        
                        return {
                            "is_success": True,
                            "data": structured_results,
                            "pdf_path": os.path.basename(pdf_path),  # Only return filename
                            "pdf_directory": "C:\\Users\\Aditya\\Desktop\\pdf reports"  # Add PDF directory info
                        }
                except Exception as e:
                    logger.warning(f"YOLO extraction failed, falling back to OCR: {str(e)}")
            
            # Fallback to direct OCR
            recognized_text = extract_text_with_easyocr(temp_path)
            
            # Process OCR results
            lines = split_ocr_text_into_lines(recognized_text)
            structured_results = extract_structured_lab_data(lines)
            data = [format_result(r) for r in structured_results]
            
            # Generate PDF report with automatic path generation
            pdf_path = create_lab_report_pdf(data, patient_name)
            
            return {
                "is_success": True,
                "data": data,
                "pdf_path": os.path.basename(pdf_path)  # Only return filename
            }
            
        finally:
            # Clean up temporary file
            if os.path.exists(temp_path):
                os.remove(temp_path)
                
    except Exception as e:
        logger.error(f"Error processing request: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={
                "is_success": False,
                "error": "Error processing the lab report image"
            }
        )

# Add a new endpoint to download the generated PDF
@app.get("/download-pdf/{pdf_filename}")
async def download_pdf(pdf_filename: str):
    """Download a generated PDF report."""
    # Use the external PDF directory
    pdf_path = os.path.join("C:\\Users\\Aditya\\Desktop\\pdf reports", pdf_filename)
    
    # Validate the path is within the allowed directory
    if not os.path.normpath(pdf_path).startswith("C:\\Users\\Aditya\\Desktop\\pdf reports"):
        raise HTTPException(status_code=400, detail="Invalid PDF path")
        
    if os.path.exists(pdf_path):
        return FileResponse(
            pdf_path,
            media_type="application/pdf",
            filename=pdf_filename
        )
    raise HTTPException(status_code=404, detail="PDF file not found")

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": "Invalid request format or data. Please check your request and try again."}
    )

@app.get("/health")
async def health_check():
    return {"status": "healthy", "message": "Lab test extractor is running"}

@app.get("/")
async def root():
    return {
        "message": "Lab Test Extractor API",
        "version": "3.0",
        "endpoints": {
            "POST /extract-lab-tests": "Extract raw lab test results from image",
            "GET /health": "Health check",
            "GET /": "API information"
        }
    }

def format_result(res):
    """Format a test result with improved out-of-range detection."""
    # Get the raw value and any flag
    test_value = res.get("value", "")
    flag = res.get("flag", "")
    
    # Handle the case where the value might include a flag
    if isinstance(test_value, str):
        test_value = test_value.replace('*', '').strip()
    
    return {
        "test_name": res.get("test_name"),
        "test_value": test_value,
        "bio_reference_range": res.get("ref_range"),
        "test_unit": res.get("unit"),
        "lab_test_out_of_range": is_test_out_of_range(
            test_value,
            res.get("ref_range"),
            flag
        )
    }

def process_yolo_results(results, image):
    """Process YOLO detection results and extract structured data."""
    detections = []
    
    # Convert image to CUDA if available
    if CUDA_AVAILABLE:
        image_tensor = torch.from_numpy(image).cuda()
    
    for i, box in enumerate(results.boxes):
        cls_id = int(box.cls[0])
        confidence = float(box.conf[0])
        label = CLASS_NAMES[cls_id]
        x1, y1, x2, y2 = map(int, box.xyxy[0])
        
        # Crop the detected region
        crop = image[y1:y2, x1:x2]
        
        # Save crop temporarily for OCR
        temp_path = f"temp_crop_{i}.png"
        cv2.imwrite(temp_path, crop)
        
        # Extract text from the crop
        ocr_text = extract_text_with_easyocr(temp_path)
        os.remove(temp_path)
        
        if ocr_text.strip():
            detections.append({
                'label': label,
                'text': ocr_text.strip(),
                'bbox': (x1, y1, x2, y2),
                'confidence': confidence,
                'y_center': (y1 + y2) / 2
            })
    
    # Clean up CUDA memory if used
    if CUDA_AVAILABLE:
        del image_tensor
        torch.cuda.empty_cache()
    
    # Group detections by rows
    rows = group_detections_by_rows(detections)
    
    # Process each row
    results = []
    for row_detections in rows:
        result = extract_test_data_from_row(row_detections)
        if result:
            results.append(result)
    
    return results

def group_detections_by_rows(detections, y_tolerance=20):
    """Group detections by their Y-coordinate to identify rows."""
    if not detections:
        return []
    
    sorted_detections = sorted(detections, key=lambda x: x['y_center'])
    rows = []
    current_row = []
    current_y = sorted_detections[0]['y_center']
    
    for detection in sorted_detections:
        if abs(detection['y_center'] - current_y) <= y_tolerance:
            current_row.append(detection)
        else:
            if current_row:
                rows.append(sorted(current_row, key=lambda x: x['bbox'][0]))
            current_row = [detection]
            current_y = detection['y_center']
    
    if current_row:
        rows.append(sorted(current_row, key=lambda x: x['bbox'][0]))
    
    return rows

def extract_test_data_from_row(row_detections):
    """Extract structured test data from a row of detections."""
    field_mapping = {}
    
    for detection in row_detections:
        label = detection['label']
        text = detection['text'].strip()
        
        if label == 'Test_Name' and text:
            field_mapping['test_name'] = text
        elif label == 'Test_Value' and text:
            field_mapping['value'] = text
        elif label == 'Test_Unit' and text:
            field_mapping['unit'] = text
        elif label == 'Ref_Range' and text:
            field_mapping['ref_range'] = text
        elif label == 'Flag' and text:
            field_mapping['flag'] = text
    
    if field_mapping.get('test_name') and field_mapping.get('value'):
        test_value = field_mapping.get('value', '').replace('*', '').strip()
        return {
            "test_name": field_mapping.get('test_name'),
            "test_value": test_value,
            "bio_reference_range": field_mapping.get('ref_range'),
            "test_unit": field_mapping.get('unit'),
            "lab_test_out_of_range": is_test_out_of_range(
                test_value,
                field_mapping.get('ref_range'),
                field_mapping.get('flag', '')
            )
        }
    
    return None


