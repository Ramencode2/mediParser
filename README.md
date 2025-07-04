# Lab Test Extractor

A FastAPI-based service that extracts lab test results from medical document images using OCR and intelligent parsing.

## Features

- **OCR Processing**: Uses PaddleOCR to extract text from medical document images
- **Intelligent Parsing**: Identifies lab test names, values, units, and reference ranges
- **Out-of-Range Detection**: Automatically flags tests that are outside normal ranges
- **RESTful API**: Simple HTTP endpoints for easy integration

## Setup

1. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Run the Server**:
   ```bash
   python run_server.py
   ```
   
   Or alternatively:
   ```bash
   uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
   ```

3. **Access the API**:
   - Server will be available at: `http://localhost:8000`
   - Health check: `http://localhost:8000/health`
   - API documentation: `http://localhost:8000/docs`

## API Usage

### Extract Lab Tests from Image

**Endpoint**: `POST /get-lab-tests`

**Request**: Upload an image file (PNG, JPG, JPEG, TIFF, BMP)

**Response**:
```json
{
  "filename": "lab_report.png",
  "data": [
    {
      "test_name": "Hemoglobin",
      "test_value": "14.2",
      "test_unit": "g/dL",
      "bio_reference_range": "12.0-16.0",
      "lab_test_out_of_range": false
    }
  ],
  "total_tests_found": 1
}
```

### Health Check

**Endpoint**: `GET /health`

**Response**:
```json
{
  "status": "healthy",
  "message": "Lab test extractor is running"
}
```

## Error Handling

The API includes comprehensive error handling:

- **400 Bad Request**: Invalid file type or format
- **500 Internal Server Error**: OCR processing or parsing errors
- **Graceful degradation**: Returns empty results if no text can be extracted

## Troubleshooting

### Common Issues

1. **PaddleOCR compilation warning**: This is normal and doesn't affect functionality
2. **"tuple index out of range"**: Fixed in recent updates - ensure you're using the latest code
3. **Server crashes**: Check that all dependencies are installed correctly

### Performance Tips

- Use high-quality images for better OCR results
- Ensure images are properly oriented
- For large documents, consider preprocessing to improve text clarity

## Development

The project structure:
```
lab extractor/
├── app/
│   ├── main.py          # FastAPI application
│   ├── ocr_utils.py     # OCR processing utilities
│   ├── parser.py        # Lab test parsing logic
│   └── test_terms.csv   # Database of lab test names
├── temp_uploads/        # Temporary file storage
├── run_server.py        # Server startup script
├── requirements.txt     # Python dependencies
└── README.md           # This file
``` 