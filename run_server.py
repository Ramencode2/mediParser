#!/usr/bin/env python3
"""
Lab Test Extractor Server Startup Script
"""

import uvicorn
import os
import sys

def main():
    # Add the current directory to Python path
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    
    # Server configuration
    host = "0.0.0.0"
    port = 8000
    reload = True  # Enable auto-reload for development
    
    print(f"[INFO] Starting Lab Test Extractor server on {host}:{port}")
    print(f"[INFO] Auto-reload: {'enabled' if reload else 'disabled'}")
    
    try:
        uvicorn.run(
            "app.main:app",
            host=host,
            port=port,
            reload=reload,
            log_level="info"
        )
    except KeyboardInterrupt:
        print("\n[INFO] Server stopped by user")
    except Exception as e:
        print(f"[ERROR] Failed to start server: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 