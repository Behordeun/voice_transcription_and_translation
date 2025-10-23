#!/bin/bash
# Install all dependencies for voice translation system

set -e

echo "============================================================"
echo "Installing Voice Translation System Dependencies"
echo "============================================================"

# Check if running as root
if [ "$EUID" -eq 0 ]; then 
    echo "⚠ Please don't run as root. Run as regular user."
    exit 1
fi

# Install system dependencies
echo ""
echo "1. Installing system dependencies..."
echo "============================================================"
sudo apt-get update
sudo apt-get install -y ffmpeg libsndfile1 portaudio19-dev

# Verify ffmpeg
if command -v ffmpeg &> /dev/null; then
    echo "✓ ffmpeg installed: $(ffmpeg -version | head -n1)"
else
    echo "✗ ffmpeg installation failed"
    exit 1
fi

# Check Python version
echo ""
echo "2. Checking Python version..."
echo "============================================================"
PYTHON_VERSION=$(python3 --version | cut -d' ' -f2 | cut -d'.' -f1,2)
echo "Python version: $PYTHON_VERSION"

if [ ! -f ".python-version" ]; then
    echo "3.11" > .python-version
fi

# Create virtual environment if it doesn't exist
echo ""
echo "3. Setting up Python virtual environment..."
echo "============================================================"
if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo "✓ Virtual environment created"
else
    echo "✓ Virtual environment already exists"
fi

# Activate virtual environment
source venv/bin/activate

# Upgrade pip
echo ""
echo "4. Upgrading pip..."
echo "============================================================"
pip install --upgrade pip setuptools wheel

# Install Python dependencies
echo ""
echo "5. Installing Python packages..."
echo "============================================================"
pip install -r requirements.txt

# Verify critical packages
echo ""
echo "6. Verifying installation..."
echo "============================================================"

python3 << 'EOF'
import sys

packages = [
    'numpy',
    'librosa',
    'torch',
    'whisper',
    'transformers',
    'fastapi',
    'websockets'
]

failed = []
for pkg in packages:
    try:
        __import__(pkg)
        print(f"✓ {pkg}")
    except ImportError:
        print(f"✗ {pkg}")
        failed.append(pkg)

if failed:
    print(f"\n✗ Failed to import: {', '.join(failed)}")
    sys.exit(1)
else:
    print("\n✓ All critical packages installed successfully")
EOF

# Run diagnostics
echo ""
echo "7. Running diagnostics..."
echo "============================================================"
python3 diagnose_audio.py

echo ""
echo "============================================================"
echo "✓ Installation complete!"
echo "============================================================"
echo ""
echo "Next steps:"
echo "  1. Activate virtual environment: source venv/bin/activate"
echo "  2. Start server: uvicorn voice_translation.api.main:app --reload"
echo "  3. Open browser: http://localhost:8000"
echo ""
