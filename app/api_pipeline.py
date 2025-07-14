# api_pipeline.py
from fastapi import FastAPI, File, UploadFile
from fastapi.responses import JSONResponse
import cv2
import numpy as np
import os
from ultralytics import YOLO
from app.ocr_utils import extract_text_with_easyocr, clean_ocr_text, parse_lab_test_line
from app.parser import MedicalDocumentParser
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

# Load model and parser
model = YOLO("C:/Users/Aditya/Desktop/lab_report_yolo_dataset/runs/detect/train3/weights/best.pt")
parser = MedicalDocumentParser()

CLASS_NAMES = ['Test_Name', 'Test_Value', 'Test_Unit', 'Flag', 'Ref_Range']

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "message": "Lab report extractor is running"}

@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "message": "Lab Report Extractor API",
        "version": "1.0",
        "endpoints": {
            "POST /predict": "Extract lab test data from image",
            "POST /debug-extract": "Debug extraction with detailed info",
            "GET /health": "Health check",
            "GET /": "API information"
        }
    }

@app.post("/predict")
async def predict_lab_report(file: UploadFile = File(...)):
    contents = await file.read()
    nparr = np.frombuffer(contents, np.uint8)
    image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

    results = model(image)[0]
    
    # Extract all detected bounding boxes with their classes and confidence scores
    detections = []
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
                'y_center': (y1 + y2) / 2  # For row alignment
            })
    
    logger.info(f"Detected {len(detections)} text regions")
    
    # Group detections by rows based on Y-coordinate
    rows = group_detections_by_rows(detections)
    
    # Process each row to extract structured data
    extracted_results = []
    for row_idx, row_detections in enumerate(rows):
        logger.info(f"Processing row {row_idx}: {row_detections}")
        
        # Try multiple approaches to extract test data from this row
        result = extract_test_data_from_row(row_detections, row_idx)
        if result:
            extracted_results.append(result)
    
    # If no structured results found, try fallback approach
    if not extracted_results:
        logger.info("No structured results found, trying fallback approach")
        extracted_results = fallback_extraction(detections)
    
    return JSONResponse(content=extracted_results)

@app.post("/debug-extract")
async def debug_extract_lab_report(file: UploadFile = File(...)):
    """Debug endpoint that returns detailed information about the extraction process."""
    contents = await file.read()
    nparr = np.frombuffer(contents, np.uint8)
    image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

    results = model(image)[0]
    
    # Extract all detected bounding boxes with their classes and confidence scores
    detections = []
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
        
        detections.append({
            'label': label,
            'text': ocr_text.strip(),
            'bbox': (x1, y1, x2, y2),
            'confidence': confidence,
            'y_center': (y1 + y2) / 2
        })
    
    # Group detections by rows
    rows = group_detections_by_rows(detections)
    
    # Process each row with detailed logging
    debug_info = {
        'total_detections': len(detections),
        'detections': detections,
        'rows': [],
        'final_results': []
    }
    
    for row_idx, row_detections in enumerate(rows):
        row_info = {
            'row_index': row_idx,
            'detections': row_detections,
            'reconstructed_text': reconstruct_row_text(row_detections),
            'field_mapping': map_detections_to_fields(row_detections),
            'parsing_attempts': []
        }
        
        # Try different parsing strategies
        row_text = reconstruct_row_text(row_detections)
        if row_text:
            cleaned_text = clean_ocr_text(row_text)
            row_info['cleaned_text'] = cleaned_text
            
            # Try medical parser
            result = parser.extract_test_data_from_line(cleaned_text)
            if result:
                row_info['parsing_attempts'].append({
                    'method': 'medical_parser',
                    'success': True,
                    'result': result.__dict__
                })
            
            # Try OCR utils parser
            parsed = parse_lab_test_line(cleaned_text)
            if parsed:
                row_info['parsing_attempts'].append({
                    'method': 'ocr_utils_parser',
                    'success': True,
                    'result': parsed
                })
        
        debug_info['rows'].append(row_info)
    
    # Try fallback extraction
    fallback_results = fallback_extraction(detections)
    debug_info['fallback_results'] = fallback_results
    
    return JSONResponse(content=debug_info)

def group_detections_by_rows(detections, y_tolerance=20):
    """Group detections by their Y-coordinate to identify rows."""
    if not detections:
        return []
    
    # Sort by Y-coordinate
    sorted_detections = sorted(detections, key=lambda x: x['y_center'])
    
    rows = []
    current_row = []
    current_y = sorted_detections[0]['y_center']
    
    for detection in sorted_detections:
        if abs(detection['y_center'] - current_y) <= y_tolerance:
            current_row.append(detection)
        else:
            if current_row:
                rows.append(current_row)
            current_row = [detection]
            current_y = detection['y_center']
    
    if current_row:
        rows.append(current_row)
    
    return rows

def extract_test_data_from_row(row_detections, row_idx):
    """Extract test data from a row of detections using multiple strategies."""
    
    # Strategy 1: Try to reconstruct the full row text and parse it
    row_text = reconstruct_row_text(row_detections)
    if row_text:
        logger.info(f"Row {row_idx} reconstructed text: {row_text}")
        
        # Clean the text
        cleaned_text = clean_ocr_text(row_text)
        
        # Try parsing with the medical parser
        result = parser.extract_test_data_from_line(cleaned_text)
        if result:
            return {
                "test_name": result.test_name,
                "test_value": result.value,
                "bio_reference_range": result.reference_range,
                "test_unit": result.unit,
                "lab_test_out_of_range": result.flag in ['H', 'L', '*']
            }
    
    # Strategy 2: Try to match individual detections to fields
    field_mapping = map_detections_to_fields(row_detections)
    if field_mapping:
        return create_result_from_fields(field_mapping)
    
    # Strategy 3: Use OCR utils parser
    if row_text:
        cleaned_text = clean_ocr_text(row_text)
        parsed = parse_lab_test_line(cleaned_text)
        if parsed:
            return {
                "test_name": parsed.get("test_name"),
                "test_value": parsed.get("value"),
                "bio_reference_range": parsed.get("ref_range"),
                "test_unit": parsed.get("unit"),
                "lab_test_out_of_range": parsed.get("flag") in ['H', 'L', '*']
            }
    
    return None

def reconstruct_row_text(row_detections):
    """Reconstruct the full text of a row from individual detections."""
    # Sort detections by X-coordinate (left to right)
    sorted_detections = sorted(row_detections, key=lambda x: x['bbox'][0])
    
    # Combine all text from the row
    texts = []
    for detection in sorted_detections:
        texts.append(detection['text'])
    
    return " ".join(texts)

def map_detections_to_fields(row_detections):
    """Map individual detections to specific fields based on their labels."""
    field_mapping = {}
    
    for detection in row_detections:
        label = detection['label']
        text = detection['text']
        
        if label == 'Test_Name' and not field_mapping.get('test_name'):
            field_mapping['test_name'] = text
        elif label == 'Test_Value' and not field_mapping.get('test_value'):
            field_mapping['test_value'] = text
        elif label == 'Test_Unit' and not field_mapping.get('test_unit'):
            field_mapping['test_unit'] = text
        elif label == 'Ref_Range' and not field_mapping.get('ref_range'):
            field_mapping['ref_range'] = text
        elif label == 'Flag' and not field_mapping.get('flag'):
            field_mapping['flag'] = text
    
    return field_mapping

def create_result_from_fields(field_mapping):
    """Create a result dictionary from field mappings."""
    return {
        "test_name": field_mapping.get('test_name'),
        "test_value": field_mapping.get('test_value'),
        "bio_reference_range": field_mapping.get('ref_range'),
        "test_unit": field_mapping.get('test_unit'),
        "lab_test_out_of_range": field_mapping.get('flag') in ['H', 'L', '*']
    }

def fallback_extraction(detections):
    """Fallback extraction when structured parsing fails."""
    results = []
    
    # Group all detections by approximate Y-coordinate
    y_groups = {}
    for detection in detections:
        y_key = round(detection['y_center'] / 20) * 20  # Group by 20-pixel intervals
        if y_key not in y_groups:
            y_groups[y_key] = []
        y_groups[y_key].append(detection)
    
    # Process each group
    for y_key, group_detections in y_groups.items():
        # Sort by X-coordinate
        sorted_detections = sorted(group_detections, key=lambda x: x['bbox'][0])
        
        # Combine text
        combined_text = " ".join([d['text'] for d in sorted_detections])
        
        # Try to parse with medical parser
        result = parser.extract_test_data_from_line(combined_text)
        if result:
            results.append({
                "test_name": result.test_name,
                "test_value": result.value,
                "bio_reference_range": result.reference_range,
                "test_unit": result.unit,
                "lab_test_out_of_range": result.flag in ['H', 'L', '*']
            })
    
    return results
