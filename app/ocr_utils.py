# app/ocr_utils.py
import os
import cv2
import numpy as np
from typing import Optional, Tuple, List
import time

# Try to import PaddleOCR
try:
    from paddleocr import PaddleOCR
    PADDLEOCR_AVAILABLE = True
    print("[INFO] PaddleOCR is available")
except ImportError:
    PADDLEOCR_AVAILABLE = False
    print("[WARNING] PaddleOCR not available, falling back to Tesseract")

# Try to import Tesseract
try:
    import pytesseract
    TESSERACT_AVAILABLE = True
    print("[INFO] Tesseract is available")
except ImportError:
    TESSERACT_AVAILABLE = False
    print("[WARNING] Tesseract not available")

# Initialize PaddleOCR model
ocr_model = None
if PADDLEOCR_AVAILABLE:
    try:
        ocr_model = PaddleOCR(use_angle_cls=True, lang='en')
        print("[INFO] PaddleOCR model initialized successfully")
    except Exception as e:
        print(f"[ERROR] Failed to initialize PaddleOCR: {e}")
        PADDLEOCR_AVAILABLE = False

def preprocess_image_for_ocr(image):
    """Enhanced preprocessing for better OCR results"""
    # Convert to grayscale if needed
    if len(image.shape) == 3:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    else:
        gray = image
    
    # Noise reduction
    denoised = cv2.fastNlMeansDenoising(gray)
    
    # Enhance contrast using CLAHE
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
    enhanced = clahe.apply(denoised)
    
    # Adaptive thresholding (better than fixed threshold)
    binary = cv2.adaptiveThreshold(
        enhanced, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
        cv2.THRESH_BINARY, 11, 2
    )
    
    # Morphological operations to clean up text
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (1, 1))
    cleaned = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel)
    
    return cv2.cvtColor(cleaned, cv2.COLOR_GRAY2BGR)

def extract_text_multiscale(image_path):
    """Try OCR at different scales for better results"""
    image = cv2.imread(image_path, cv2.IMREAD_COLOR)
    if image is None:
        print(f"[ERROR] Could not read image: {image_path}")
        return ""
    
    results = []
    scales = [1.0, 1.5, 2.0]  # Try original, 1.5x, and 2x scaling
    
    for scale in scales:
        try:
            if scale != 1.0:
                height, width = image.shape[:2]
                new_height, new_width = int(height * scale), int(width * scale)
                scaled_image = cv2.resize(image, (new_width, new_height), interpolation=cv2.INTER_CUBIC)
            else:
                scaled_image = image
            
            processed_image = preprocess_image_for_ocr(scaled_image)
            result = ocr_model.predict(processed_image)
            
            # Extract text from result
            text_lines = []
            for page_result in result:
                if hasattr(page_result, 'rec_texts'):
                    text_lines.extend([text.strip() for text in page_result.rec_texts if text.strip()])
            
            if text_lines:
                full_text = "\n".join(text_lines)
                results.append((scale, full_text, len(text_lines)))
                print(f"[DEBUG] Scale {scale}: {len(text_lines)} lines extracted")
                
        except Exception as e:
            print(f"[WARNING] Scale {scale} failed: {e}")
            continue
    
    # Return the result with most extracted text
    if results:
        best_result = max(results, key=lambda x: x[2])
        print(f"[INFO] Best OCR result at scale {best_result[0]} with {best_result[2]} lines")
        return best_result[1]
    
    return ""

def extract_text_with_tesseract(image_path):
    """Extract text using Tesseract OCR"""
    if not TESSERACT_AVAILABLE:
        return ""
    
    try:
        # Read and preprocess image
        image = cv2.imread(image_path, cv2.IMREAD_COLOR)
        if image is None:
            return ""
        
        processed_image = preprocess_image_for_ocr(image)
        
        # Convert back to grayscale for Tesseract
        gray = cv2.cvtColor(processed_image, cv2.COLOR_BGR2GRAY)
        
        # Extract text with Tesseract
        text = pytesseract.image_to_string(gray, config='--psm 6')
        return text.strip()
        
    except Exception as e:
        print(f"[ERROR] Tesseract OCR failed: {e}")
        return ""

def extract_text_simple_fallback(image_path):
    """Simple fallback OCR method"""
    try:
        image = cv2.imread(image_path, cv2.IMREAD_COLOR)
        if image is None:
            return ""
        
        # Basic preprocessing
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        
        if TESSERACT_AVAILABLE:
            return pytesseract.image_to_string(binary, config='--psm 6').strip()
        else:
            return ""
            
    except Exception as e:
        print(f"[ERROR] Simple fallback failed: {e}")
        return ""

def count_medical_terms(text):
    """Count likely medical terms to help select best OCR result"""
    medical_indicators = [
        'mg/dl', 'g/dl', 'μmol/l', 'iu/l', 'cells', 'count', 'level', 
        'test', 'normal', 'high', 'low', 'hemoglobin', 'platelet', 
        'sodium', 'potassium', 'glucose', 'creatinine', 'bilirubin',
        'wbc', 'rbc', 'hgb', 'hct', 'mcv', 'mch', 'mchc', 'rdw'
    ]
    text_lower = text.lower()
    return sum(1 for term in medical_indicators if term in text_lower)

def extract_text_from_image(image_path):
    """Enhanced OCR with confidence-based selection"""
    if not os.path.exists(image_path):
        print(f"[ERROR] Image file does not exist: {image_path}")
        return ""
    
    results = []
    
    # Try PaddleOCR with multi-scale
    if PADDLEOCR_AVAILABLE and ocr_model is not None:
        try:
            result = extract_text_multiscale(image_path)
            if result.strip():
                word_count = len(result.split())
                medical_terms = count_medical_terms(result)
                results.append(("PaddleOCR", result, word_count, medical_terms))
                print(f"[INFO] PaddleOCR extracted {word_count} words, {medical_terms} medical terms")
        except Exception as e:
            print(f"[ERROR] PaddleOCR failed: {e}")
    
    # Try Tesseract fallback
    if TESSERACT_AVAILABLE:
        try:
            result = extract_text_with_tesseract(image_path)
            if result.strip():
                word_count = len(result.split())
                medical_terms = count_medical_terms(result)
                results.append(("Tesseract", result, word_count, medical_terms))
                print(f"[INFO] Tesseract extracted {word_count} words, {medical_terms} medical terms")
        except Exception as e:
            print(f"[ERROR] Tesseract failed: {e}")
    
    # Select best result based on word count and medical terms
    if results:
        # Prefer result with more words and medical terms
        best_result = max(results, key=lambda x: x[2] + x[3] * 2)  # Weight medical terms more
        print(f"[INFO] Selected {best_result[0]} result with {best_result[2]} words and {best_result[3]} medical terms")
        return best_result[1]
    
    # Final fallback
    fallback_result = extract_text_simple_fallback(image_path)
    if fallback_result:
        print("[INFO] Using simple fallback OCR")
        return fallback_result
    
    print("[WARNING] No OCR method succeeded")
    return ""

def extract_text_with_paddleocr(image_path):
    """Extract text using PaddleOCR with robust error handling"""
    
    try:
        # Read image in color (not grayscale) to avoid PaddleOCR internal errors
        image = cv2.imread(image_path, cv2.IMREAD_COLOR)
        if image is None:
            print(f"[ERROR] cv2 could not read image at path: {image_path}")
            return ""

        # Convert to grayscale for preprocessing
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        # Preprocess the grayscale image for better OCR results
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)
        _, binary_image = cv2.threshold(blurred, 128, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)
        
        # Optional: Add dilation and erotion to improve text readability
        kernel = np.ones((3, 3), np.uint8)
        dilated_image = cv2.dilate(binary_image, kernel, iterations=1)
        eroded_image = cv2.erode(dilated_image, kernel, iterations=1)

        # Convert back to color for PaddleOCR (it expects 3-channel images)
        color_image = cv2.cvtColor(eroded_image, cv2.COLOR_GRAY2BGR)

        # Use predict method for PaddleOCR 3.0.3
        result = ocr_model.predict(color_image)

        lines = []
        print("\n[OCR OUTPUT START]")
        print(f"OCR Result Type: {type(result)}")
        print(f"OCR Result Length: {len(result)}")
        
        if not result or len(result) == 0:
            print("[WARNING] PaddleOCR returned empty result.")
            return ""
        
        # Handle PaddleOCR 3.0.3 result structure
        for page_idx, page_result in enumerate(result):
            print(f"\nPage {page_idx} Result:")
            print(f"  Page Result Type: {type(page_result)}")
            
            # Extract rec_texts from the result
            if hasattr(page_result, 'rec_texts'):
                rec_texts = page_result.rec_texts
                print(f"  Found {len(rec_texts)} text lines")
                
                for text_idx, text in enumerate(rec_texts):
                    if text and len(text.strip()) > 1:
                        print(f"    [OCR Line {text_idx}] {text}")
                        lines.append(text.strip())
            else:
                print("  No rec_texts found in result")
                # Try to access as dictionary
                if isinstance(page_result, dict) and 'rec_texts' in page_result:
                    rec_texts = page_result['rec_texts']
                    for text in rec_texts:
                        if text and len(text.strip()) > 1:
                            lines.append(text.strip())

        print("[OCR OUTPUT END]\n")
        print("Extracted OCR Lines:\n", "\n".join(lines))  # Manual print of extracted lines
        
        return "\n".join(lines)
        
    except Exception as e:
        print(f"[ERROR] Error in extract_text_with_paddleocr: {e}")
        import traceback
        traceback.print_exc()
        return ""
