# app/main.py

import os
import time
from fastapi import FastAPI, UploadFile, File
from fastapi.responses import JSONResponse
from app.ocr_utils import extract_text_with_easyocr, clean_ocr_text, parse_lab_test_line, extract_structured_lab_data
from app.parser import MedicalDocumentParser
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
async def extract_lab_tests(file: UploadFile = File(...)):
    """Legacy endpoint using direct OCR."""
    print("Received file:", file.filename, "Content-Type:", file.content_type)
    if not file.content_type or not file.content_type.startswith("image/"):
        return JSONResponse(status_code=400, content={"is_success": False, "error": f"Uploaded file must be an image. Received content type: {file.content_type}"})
    try:
        temp_path = f"_temp_{file.filename}"
        with open(temp_path, "wb") as f:
            f.write(await file.read())
            
        # Try YOLO-based extraction first if available
        if YOLO_AVAILABLE:
            try:
                image = cv2.imread(temp_path)
                results = model(image)[0]
                structured_results = process_yolo_results(results, image)
                if structured_results:
                    os.remove(temp_path)
                    return {
                        "is_success": True,
                        "data": structured_results
                    }
            except Exception as e:
                logger.warning(f"YOLO extraction failed, falling back to OCR: {str(e)}")
        
        # Fallback to direct OCR
        ocr_start = time.time()
        recognized_text = extract_text_with_easyocr(temp_path)
        ocr_time = time.time() - ocr_start
        os.remove(temp_path)

        # Split OCR text into lines and extract structured data
        from app.ocr_utils import split_ocr_text_into_lines, extract_structured_lab_data
        lines = split_ocr_text_into_lines(recognized_text)
        structured_results = extract_structured_lab_data(lines)

        # Format output as per the first image
        def format_result(res):
            # Determine out of range if possible
            out_of_range = False
            try:
                if res.get("ref_range") and res.get("value"):
                    ref = res["ref_range"].replace(" ", "")
                    if "-" in ref:
                        low, high = ref.split("-")
                        val = float(res["value"])
                        low = float(low)
                        high = float(high)
                        out_of_range = not (low <= val <= high)
            except Exception:
                out_of_range = False
            return {
                "test_name": res.get("test_name"),
                "test_value": res.get("value"),
                "bio_reference_range": res.get("ref_range"),
                "test_unit": res.get("unit"),
                "lab_test_out_of_range": out_of_range
            }
        data = [format_result(r) for r in structured_results]
        return {
            "is_success": True,
            "data": data
        }
    except Exception as e:
        import traceback
        traceback.print_exc()
        return JSONResponse(status_code=500, content={"is_success": False, "error": str(e)})


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
        return {
            "test_name": field_mapping.get('test_name'),
            "test_value": field_mapping.get('value'),
            "bio_reference_range": field_mapping.get('ref_range'),
            "test_unit": field_mapping.get('unit'),
            "lab_test_out_of_range": field_mapping.get('flag', '').upper() in ['H', 'L', '*']
        }
    
    return None
