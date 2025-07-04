#!/usr/bin/env python3
"""
Debug script for PaddleOCR output structure
"""

import os
import sys
import json
from paddleocr import PaddleOCR

def debug_ocr_structure(image_path):
    """Debug the PaddleOCR output structure for a given image"""
    
    if not os.path.exists(image_path):
        print(f"[ERROR] Image file does not exist: {image_path}")
        return
    
    try:
        # Initialize PaddleOCR
        print("[INFO] Initializing PaddleOCR...")
        ocr_model = PaddleOCR(use_angle_cls=True, lang='en')
        
        # Read and process image
        print(f"[INFO] Processing image: {image_path}")
        result = ocr_model.predict(image_path)
        
        print("\n" + "="*50)
        print("PADDLEOCR DEBUG OUTPUT")
        print("="*50)
        
        print(f"Result type: {type(result)}")
        print(f"Result length: {len(result)}")
        print(f"Result: {json.dumps(result, indent=2, default=str)}")
        
        # Analyze structure
        print("\n" + "="*50)
        print("STRUCTURE ANALYSIS")
        print("="*50)
        
        for page_idx, page_blocks in enumerate(result):
            print(f"\nPage {page_idx}:")
            print(f"  Type: {type(page_blocks)}")
            print(f"  Length: {len(page_blocks)}")
            
            if len(page_blocks) > 0:
                print(f"  First block type: {type(page_blocks[0])}")
                print(f"  First block length: {len(page_blocks[0]) if hasattr(page_blocks[0], '__len__') else 'N/A'}")
                print(f"  First block content: {page_blocks[0]}")
                
                # Check if first block has elements
                if hasattr(page_blocks[0], '__len__') and len(page_blocks[0]) > 0:
                    print(f"  First block[0] type: {type(page_blocks[0][0])}")
                    print(f"  First block[0] content: {page_blocks[0][0]}")
        
        print("\n" + "="*50)
        print("EXTRACTION TEST")
        print("="*50)
        
        # Test our extraction logic
        lines = []
        for page_idx, page_blocks in enumerate(result):
            for block_idx, block in enumerate(page_blocks):
                try:
                    text = None
                    
                    # Case 1: Block is a list/tuple with text at index 0
                    if isinstance(block, (list, tuple)) and len(block) > 0:
                        if isinstance(block[0], str):
                            text = block[0].strip()
                        elif isinstance(block[0], (list, tuple)) and len(block[0]) > 0:
                            text = str(block[0][0]).strip()
                    
                    # Case 2: Block is a string directly
                    elif isinstance(block, str):
                        text = block.strip()
                    
                    # Case 3: Block is a dictionary with text key
                    elif isinstance(block, dict):
                        text = block.get('text', '').strip()
                    
                    # Case 4: Try to convert to string
                    else:
                        text = str(block).strip()
                    
                    if text and len(text) > 1:
                        print(f"✓ Extracted: '{text}'")
                        lines.append(text)
                    else:
                        print(f"✗ Skipped: '{text}'")
                        
                except Exception as e:
                    print(f"✗ Error processing block {block_idx}: {e}")
        
        print(f"\nTotal lines extracted: {len(lines)}")
        print("Extracted text:")
        for i, line in enumerate(lines):
            print(f"  {i+1}: {line}")
            
    except Exception as e:
        print(f"[ERROR] Debug failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python debug_ocr.py <image_path>")
        sys.exit(1)
    
    image_path = sys.argv[1]
    debug_ocr_structure(image_path) 