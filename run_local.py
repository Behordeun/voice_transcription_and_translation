#!/usr/bin/env python3
"""Run the voice translation system locally without Docker"""
import os
import sys
import subprocess
from pathlib import Path

def main():
    # Set production environment
    os.environ["PRODUCTION"] = "true"
    os.environ["TORCH_NUM_THREADS"] = "2"
    os.environ["OMP_NUM_THREADS"] = "2"
    
    # Create logs directory
    Path("logs").mkdir(exist_ok=True)
    
    # Run the FastAPI server
    try:
        subprocess.run([
            sys.executable, "-m", "uvicorn",
            "voice_translation.api.main:app",
            "--host", "0.0.0.0",
            "--port", "8000",
            "--workers", "1"
        ], check=True)
    except KeyboardInterrupt:
        print("\nShutting down...")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()