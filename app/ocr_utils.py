# app/ocr_utils.py
import os
import cv2
import easyocr
import re
import torch
from typing import List, Dict, Optional, Any
import logging

logger = logging.getLogger(__name__)

# Initialize EasyOCR reader once
CUDA_AVAILABLE = torch.cuda.is_available()
reader = easyocr.Reader(['en'], gpu=CUDA_AVAILABLE)
logger.info(f"Initialized EasyOCR with GPU support: {CUDA_AVAILABLE}")

def extract_text_with_easyocr(image_path):
    """Extract text from an image using EasyOCR with enhanced error handling."""
    try:
        image = cv2.imread(image_path)
        if image is None:
            logger.error(f"Could not read image: {image_path}")
            return ""
        
        # Check if image is too small or empty
        if image.size == 0 or image.shape[0] < 10 or image.shape[1] < 10:
            logger.warning(f"Image too small or empty: {image_path}")
            return ""
        
        # Use the global reader instance
        result = reader.readtext(image, detail=0, paragraph=True)
        
        # Log the result for debugging
        logger.info(f"EasyOCR result for {image_path}: {result}")
        
        combined = " ".join(result)
        return combined.strip()
        
    except Exception as e:
        logger.error(f"Error in OCR extraction for {image_path}: {str(e)}")
        return ""

def extract_text_with_easyocr_from_crop(image_path, bbox=None):
    """Extract text from a specific crop of an image."""
    try:
        image = cv2.imread(image_path)
        if image is None:
            return ""
        
        if bbox:
            x1, y1, x2, y2 = bbox
            crop = image[y1:y2, x1:x2]
        else:
            crop = image
        
        # Save crop temporarily
        temp_crop_path = f"temp_crop_{os.getpid()}.png"
        cv2.imwrite(temp_crop_path, crop)
        
        # Extract text
        text = extract_text_with_easyocr(temp_crop_path)
        
        # Clean up
        if os.path.exists(temp_crop_path):
            os.remove(temp_crop_path)
        
        return text
        
    except Exception as e:
        logger.error(f"Error in crop OCR extraction: {str(e)}")
        return ""

def clean_ocr_text(text):
    """
    Enhanced OCR text cleaning with medical-specific corrections.
    """
    if not text:
        return ""
    
    # Convert to lowercase for consistency
    text = text.lower()
    
    # Enhanced medical-specific OCR corrections
    corrections = [
        # Common OCR character misreads
        (r"gmldl", "gm/dl"),
        (r"mgldl", "mg/dl"),
        (r"mmolll", "mmol/l"),
        (r"millll", "mmol/l"),
        (r"milll", "mmol/l"),
        (r"melhod", "method"),
        (r"melfiod", "method"),
        (r"melfiod", "method"),
        (r"TESL", "TEST"),
        (r"RETUSERUM", "SERUM"),
        (r"JRIC", "URIC"),
        (r"omocresol", "bromocresol"),
        (r"pholomelric", "photometric"),
        (r"delermination", "determination"),
        (r"compensalion", "compensation"),
        (r"calciilated", "calculated"),
        (r"calciulated", "calculated"),
        (r"biuret", "biuret"),
        (r"meihod", "method"),
        (r"melliod", "method"),
        (r"arsenazo", "arsenazo"),
        (r"molybdale", "molybdate"),
        (r"endpoint", "endpoint"),
        (r"enzymalic", "enzymatic"),
        (r"tbhba", "TBHBA"),
        (r"glucose", "glucose"),
        (r"creatinine", "creatinine"),
        (r"urea", "urea"),
        (r"sodium", "sodium"),
        (r"potassium", "potassium"),
        (r"calcium", "calcium"),
        (r"phosphorus", "phosphorus"),
        (r"protein", "protein"),
        (r"albumin", "albumin"),
        (r"globulin", "globulin"),
        
        # Character corrections
        (r"\bO\b", "0"),  # Standalone O to 0
        (r"\bI\b", "1"),  # Standalone I to 1
        (r"\bl\b", "1"),  # lowercase l to 1
        (r"(?<=\d)O(?=\s|$)", "0"),  # O to 0 after digits
        (r"(?<=\d)o(?=\s|$)", "0"),  # o to 0 after digits
        (r"(?<!\d)S(?=\s|\d)", "5"),  # S to 5 before digits
        (r"(?<!\d)I(?=\s|\d)", "1"),  # I to 1 before digits
        
        # Unit standardizations
        (r"\bmg\s*%\s*dl\b", "mg/dl"),
        (r"\bg\s*%\s*dl\b", "g/dl"),
        (r"\bmmol\s*l\b", "mmol/l"),
        (r"\biu\s*ml\b", "iu/ml"),
        (r"\bng\s*ml\b", "ng/ml"),
        (r"\bpg\s*ml\b", "pg/ml"),
        (r"\bmcg\s*ml\b", "mcg/ml"),
        (r"\bcells\s*ul\b", "cells/ul"),
        (r"\bthousand\s*ul\b", "thousand/ul"),
        (r"\bmillion\s*ul\b", "million/ul"),
        
        # Range separators
        (r"\s*[-–]\s*", "-"),
        (r"\s*—\s*", "-"),
        (r"\s*to\s*", "-"),
        
        # Clean up spacing
        (r"\s+", " "),  # Collapse multiple spaces
        (r"\s*([:/-])\s*", r"\1"),  # Remove spaces around :/-
        (r"[^\w\s\./:-]", ""),  # Remove unwanted characters but keep dots, slashes, colons, hyphens
    ]
    
    for pattern, repl in corrections:
        text = re.sub(pattern, repl, text, flags=re.IGNORECASE)
    
    # Fix spacing around numbers and units
    text = re.sub(r'(\d)\s+([a-zA-Z/%])', r'\1 \2', text)
    text = re.sub(r'([a-zA-Z])\s+(\d)', r'\1 \2', text)
    
    # Normalize reference range separators
    text = re.sub(r'\s*[-–]\s*', '-', text)
    
    return text.strip()

def parse_lab_test_line(text):
    """
    Enhanced parsing of a cleaned lab test line into structured data.
    Returns a dict with test_name, value, unit, ref_range, flag if found.
    """
    if not text or len(text.strip()) < 5:
        return None
    
    # Enhanced comprehensive pattern for lab test results
    # Handles various formats like:
    # "MCHC 30.5* 31.5-34.5 gm/dl"
    # "UREA 24.3 19-44 mg/dl"
    # "SODIUM 138.1 135-145 mmol/l"
    # "CREATININE, SERUM 0.91 0.7-1.3"
    patterns = [
        # Pattern 1: Test Name | Value | Flag | Reference Range | Unit
        r"(?P<test_name>[a-zA-Z\s,]+?)\s+(?P<value>\d+[\.,]?\d*)\s*(?P<flag>[\*HLN])?\s*(?P<ref_range>\d+[\.,]?\d*\s*[-–]\s*\d+[\.,]?\d*)?\s*(?P<unit>[a-zA-Z/%]+)?",
        
        # Pattern 2: Test Name | Value | Reference Range | Unit
        r"(?P<test_name>[a-zA-Z\s,]+?)\s+(?P<value>\d+[\.,]?\d*)\s+(?P<ref_range>\d+[\.,]?\d*\s*[-–]\s*\d+[\.,]?\d*)\s*(?P<unit>[a-zA-Z/%]+)?",
        
        # Pattern 3: Test Name | Value | Unit | Reference Range
        r"(?P<test_name>[a-zA-Z\s,]+?)\s+(?P<value>\d+[\.,]?\d*)\s*(?P<unit>[a-zA-Z/%]+)\s+(?P<ref_range>\d+[\.,]?\d*\s*[-–]\s*\d+[\.,]?\d*)",
        
        # Pattern 4: Simple Test Name | Value
        r"(?P<test_name>[a-zA-Z\s,]+?)\s+(?P<value>\d+[\.,]?\d*)",
        
        # Pattern 5: Test Name with colon | Value | extras
        r"(?P<test_name>[a-zA-Z\s,]+?):\s*(?P<value>\d+[\.,]?\d*)\s*(?P<unit>[a-zA-Z/%]+)?\s*(?P<ref_range>\d+[\.,]?\d*\s*[-–]\s*\d+[\.,]?\d*)?",
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            test_name = match.group("test_name").strip() if match.group("test_name") else None
            value = match.group("value").replace(",", ".") if match.group("value") else None
            flag = match.group("flag") if match.group("flag") else None
            ref_range = match.group("ref_range") if match.group("ref_range") else None
            unit = match.group("unit") if match.group("unit") else None
            
            # Clean up reference range
            if ref_range:
                ref_range = ref_range.replace(" ", "").replace(",", ".")
            
            # Clean up unit
            if unit:
                unit = unit.strip()
            
            # Validate test name
            if test_name and is_valid_test_name(test_name):
                return {
                    "test_name": test_name,
                    "value": value,
                    "unit": unit,
                    "ref_range": ref_range,
                    "flag": flag
                }
    
    return None

def is_valid_test_name(name: str) -> bool:
    """Enhanced validation for test names."""
    name = name.strip()
    
    # Basic validation
    if not name or len(name) < 2:
        return False
    
    # Must contain at least one letter
    if not re.search(r'[a-zA-Z]', name):
        return False
    
    # Reject if all numbers/symbols
    if all(char in '0123456789.- /' for char in name):
        return False
    
    # Reject common false positives
    invalid_patterns = [
        r'^\d+$',  # Only numbers
        r'^[.\-\s]+$',  # Only punctuation
        r'^(ul|ml|dl|l|mg|g|ng|pg|mcg|kg|lbs)$',  # Only units
        r'^(a|an|the|and|or|of|in|on|at|to|for|with|by)$',  # Articles/prepositions
        r'^(normal|abnormal|high|low|positive|negative)$',  # Result descriptors
        r'^(page|report|lab|test|result|value|range|reference)$',  # Document terms
        r'^(date|time|patient|doctor|physician|hospital|clinic)$',  # Header terms
    ]
    
    name_lower = name.lower()
    for pattern in invalid_patterns:
        if re.match(pattern, name_lower):
            return False
    
    # Reject very short common words
    if len(name) <= 3 and name_lower in {'the', 'and', 'for', 'are', 'but', 'not', 'you', 'all', 'can', 'had', 'her', 'was', 'one', 'our', 'out', 'day', 'get', 'has', 'him', 'his', 'how', 'man', 'new', 'now', 'old', 'see', 'two', 'way', 'who', 'boy', 'did', 'its', 'let', 'put', 'say', 'she', 'too', 'use'}:
        return False
    
    return True

def extract_structured_lab_data(texts):
    """
    Enhanced function that takes a list of OCR text lines, cleans and parses them into structured lab test data.
    Returns a list of dicts with confidence scores.
    """
    results = []
    for text in texts:
        cleaned = clean_ocr_text(text)
        parsed = parse_lab_test_line(cleaned)
        if parsed:
            # Calculate confidence score
            confidence = calculate_confidence(parsed)
            parsed['confidence'] = confidence
            parsed['raw_text'] = text
            parsed['cleaned_text'] = cleaned
            results.append(parsed)
    return results

def calculate_confidence(parsed_data: Dict[str, Any]) -> float:
    """Calculate confidence score for extracted test result."""
    confidence = 0.0
    
    # Base confidence for having test name and value
    if parsed_data.get('test_name') and parsed_data.get('value'):
        confidence += 0.4
    
    # Additional confidence for complete data
    if parsed_data.get('unit'):
        confidence += 0.2
    if parsed_data.get('ref_range'):
        confidence += 0.2
    if parsed_data.get('flag'):
        confidence += 0.1
    
    # Bonus for recognized test names
    test_name_lower = parsed_data.get('test_name', '').lower()
    recognized_tests = [
        'hemoglobin', 'hematocrit', 'rbc', 'wbc', 'platelet', 'mcv', 'mch', 'mchc',
        'glucose', 'creatinine', 'urea', 'sodium', 'potassium', 'chloride', 'albumin',
        'cholesterol', 'triglycerides', 'hdl', 'ldl', 'vldl',
        'alt', 'ast', 'alp', 'bilirubin', 'ggt',
        'tsh', 't3', 't4', 'ft3', 'ft4',
        'troponin', 'ck-mb', 'bnp', 'nt-probnp',
        'hba1c', 'fasting glucose', 'random glucose', 'insulin',
        'esr', 'crp', 'procalcitonin',
        'pt', 'ptt', 'inr', 'fibrinogen', 'd-dimer',
        'protein', 'globulin', 'calcium', 'phosphorus', 'uric acid'
    ]
    
    if any(test in test_name_lower for test in recognized_tests):
        confidence += 0.1
    
    return min(confidence, 1.0)

def split_ocr_text_into_lines(text: str) -> List[str]:
    """Split OCR text into meaningful lines while preserving test result integrity."""
    if not text:
        return []
    
    # First, split by newlines
    lines = text.split('\n')
    processed_lines = []
    current_line = ''
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
            
        # Check if line looks like a complete test result
        has_value = bool(re.search(r'\d+\.?\d*', line))
        has_unit = bool(re.search(r'[a-zA-Z/%]+', line))
        
        if has_value and has_unit:
            # This might be a complete test result
            if current_line:
                processed_lines.append(current_line)
            current_line = line
        else:
            # This might be continuation of previous line
            current_line = (current_line + ' ' + line).strip()
    
    if current_line:
        processed_lines.append(current_line)
    
    return processed_lines

def clean_ocr_text(text: str) -> str:
    """Enhanced OCR text cleaning with focus on lab report formats."""
    if not text:
        return ""
    
    # Basic cleanup
    text = re.sub(r'[\r\n]+', '\n', text)
    text = re.sub(r'\s+', ' ', text)
    
    # Fix common OCR errors in lab reports
    replacements = {
        r'0(?=\s|$)': 'O',  # Fix zero to O at end of words
        r'l(?=\d)': '1',    # Fix l to 1 before numbers
        r'I(?=\d)': '1',    # Fix I to 1 before numbers
        r'S(?=\d)': '5',    # Fix S to 5 before numbers
        r'g/di': 'g/dl',    # Fix common unit error
        r'mg/di': 'mg/dl',  # Fix common unit error
        r'mlU/L': 'mIU/L',  # Fix common unit error
        r'mlU/ml': 'mIU/ml',# Fix common unit error
    }
    
    for pattern, replacement in replacements.items():
        text = re.sub(pattern, replacement, text)
    
    # Fix spacing around units
    text = re.sub(r'(\d)([a-zA-Z])', r'\1 \2', text)  # Add space between number and unit
    text = re.sub(r'\[([HL])\]', r' [\1]', text)      # Fix spacing around flags
    
    return text.strip()
