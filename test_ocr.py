#!/usr/bin/env python3
"""
Simple test script for OCR functionality
"""

import os
import sys
from app.ocr_utils import extract_text_from_image

def test_ocr_system():
    """Test the OCR system with available images"""
    
    print("Testing OCR System...")
    print("="*50)
    
    # Look for test images in the current directory
    test_images = []
    for file in os.listdir('.'):
        if file.lower().endswith(('.png', '.jpg', '.jpeg', '.tiff', '.bmp')):
            test_images.append(file)
    
    if not test_images:
        print("No test images found in current directory.")
        print("Please place an image file in the current directory to test.")
        return
    
    print(f"Found {len(test_images)} test image(s):")
    for img in test_images:
        print(f"  - {img}")
    
    print("\n" + "="*50)
    
    # Test each image
    for image_path in test_images:
        print(f"\nTesting: {image_path}")
        print("-" * 30)
        
        try:
            # Extract text
            text = extract_text_from_image(image_path)
            
            if text.strip():
                print("✓ OCR successful!")
                print(f"Extracted text length: {len(text)} characters")
                print("First 200 characters:")
                print(text[:200] + "..." if len(text) > 200 else text)
            else:
                print("✗ OCR returned empty result")
                
        except Exception as e:
            print(f"✗ OCR failed with error: {e}")
            import traceback
            traceback.print_exc()
    
    print("\n" + "="*50)
    print("Test completed!")

if __name__ == "__main__":
    test_ocr_system() 