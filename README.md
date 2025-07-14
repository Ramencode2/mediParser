# Lab Report Extractor

An AI-powered system for extracting structured lab test data from medical reports using YOLO object detection and OCR.

## Recent Improvements

### Fixed Inconsistency Issues

The main issue causing inconsistent results was in the API pipeline logic. The previous approach had several problems:

1. **Misaligned Bounding Box Processing**: YOLO detected individual bounding boxes for different field types (Test_Name, Test_Value, etc.), but the text extraction and merging logic wasn't properly handling the spatial relationships between these detections.

2. **Poor Row Grouping**: The original code tried to merge fields by index position, which failed when YOLO detections didn't align perfectly with the actual text layout.

3. **Inadequate Fallback**: When structured parsing failed, there was no robust fallback mechanism.

### New Approach

The improved pipeline now:

1. **Groups detections by Y-coordinate** to identify rows properly
2. **Uses multiple parsing strategies** for each row:
   - Reconstructs full row text and parses it
   - Maps individual detections to specific fields
   - Uses OCR utils parser as backup
3. **Provides detailed debugging** to understand extraction issues
4. **Implements robust fallback** when structured parsing fails

## API Endpoints

### POST /predict
Extract lab test data from an uploaded image.

**Response format:**
```json
[
  {
    "test_name": "Hemoglobin",
    "test_value": "15.3",
    "bio_reference_range": "11.1-14.4",
    "test_unit": "g/dl",
    "lab_test_out_of_range": true
  }
]
```

### POST /debug-extract
Debug endpoint that returns detailed information about the extraction process.

**Response includes:**
- Total number of detections
- Individual detection details (text, confidence, bounding box)
- Row grouping information
- Parsing attempts for each row
- Fallback results

## Usage

### Starting the Server

```bash
python run_server.py
```

The server will start on `http://localhost:8000`

### Testing with Debug Script

Use the debug script to understand extraction issues:

```bash
python test_debug_extraction.py path/to/lab_report.jpg
```

This will show:
- Regular extraction results
- Detailed debugging information
- Individual detection details
- Row grouping and parsing attempts

### API Documentation

Visit `http://localhost:8000/docs` for interactive API documentation.

## Troubleshooting

### Common Issues

1. **Inconsistent Results**: Use the debug endpoint to see what text is being extracted from each bounding box
2. **Missing Fields**: Check if YOLO is detecting all required field types
3. **Wrong Text Extraction**: Verify OCR is working correctly on individual crops

### Debugging Steps

1. **Use the debug endpoint**:
   ```bash
   curl -X POST "http://localhost:8000/debug-extract" \
        -H "accept: application/json" \
        -H "Content-Type: multipart/form-data" \
        -F "file=@your_lab_report.jpg"
   ```

2. **Check detection quality**: Look at the confidence scores and bounding boxes
3. **Verify text extraction**: Ensure OCR is reading text correctly from each crop
4. **Review row grouping**: Make sure detections are being grouped into rows properly

### Improving Results

1. **Retrain YOLO model** with more diverse lab report formats
2. **Adjust Y-coordinate tolerance** in `group_detections_by_rows()` function
3. **Enhance OCR preprocessing** for better text recognition
4. **Add more parsing patterns** to handle different lab report formats

## File Structure

```
lab extractor/
├── app/
│   ├── api_pipeline.py      # Main API with improved extraction logic
│   ├── ocr_utils.py         # OCR utilities with enhanced error handling
│   ├── parser.py            # Medical document parser
│   └── main.py              # FastAPI app entry point
├── test_debug_extraction.py # Debug testing script
├── run_server.py            # Server startup script
└── README.md               # This file
```

## Dependencies

- FastAPI
- OpenCV
- EasyOCR
- Ultralytics (YOLO)
- NumPy
- Uvicorn

Install with:
```bash
pip install -r requirements.txt
```