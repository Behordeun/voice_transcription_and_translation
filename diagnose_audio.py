#!/usr/bin/env python3
"""Diagnose audio processing pipeline"""

import base64
import subprocess
import sys
from pathlib import Path


def check_ffmpeg():
    """Check if ffmpeg is installed and working"""
    print("=" * 60)
    print("1. Checking ffmpeg installation...")
    print("=" * 60)
    
    try:
        result = subprocess.run(
            ['ffmpeg', '-version'],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0:
            version_line = result.stdout.split('\n')[0]
            print(f"✓ ffmpeg installed: {version_line}")
            
            # Check for opus codec support
            result = subprocess.run(
                ['ffmpeg', '-codecs'],
                capture_output=True,
                text=True,
                timeout=5
            )
            if 'opus' in result.stdout.lower():
                print("✓ Opus codec supported")
            else:
                print("⚠ Opus codec might not be supported")
            
            return True
        else:
            print("✗ ffmpeg not working properly")
            return False
    except FileNotFoundError:
        print("✗ ffmpeg not found in PATH")
        print("  Install with: sudo apt-get install ffmpeg")
        return False
    except Exception as e:
        print(f"✗ Error checking ffmpeg: {e}")
        return False


def test_webm_decode():
    """Test WebM/Opus decoding"""
    print("\n" + "=" * 60)
    print("2. Testing WebM/Opus decoding...")
    print("=" * 60)
    
    # Create a minimal WebM header (this won't be valid audio, just for testing)
    test_data = b'\x1a\x45\xdf\xa3' + b'\x00' * 100
    
    try:
        import tempfile
        import os
        
        with tempfile.NamedTemporaryFile(suffix='.webm', delete=False) as f:
            f.write(test_data)
            temp_path = f.name
        
        try:
            result = subprocess.run(
                ['ffmpeg', '-i', temp_path, '-ar', '16000', '-ac', '1', '-f', 'wav', '-'],
                capture_output=True,
                timeout=5
            )
            
            if result.returncode == 0:
                print("✓ ffmpeg can process WebM files")
            else:
                print("⚠ ffmpeg had issues with WebM (expected with test data)")
                print(f"  stderr: {result.stderr.decode()[:200]}")
        finally:
            os.unlink(temp_path)
            
    except Exception as e:
        print(f"✗ Error testing WebM decode: {e}")


def test_audio_utils():
    """Test audio_utils module"""
    print("\n" + "=" * 60)
    print("3. Testing audio_utils module...")
    print("=" * 60)
    
    try:
        from voice_translation.core.audio_utils import load_audio_data
        import numpy as np
        
        print("✓ audio_utils imported successfully")
        
        # Test with empty data
        result = load_audio_data(b'')
        if isinstance(result, np.ndarray) and len(result) == 0:
            print("✓ Empty data handling works")
        
        # Test with small data
        result = load_audio_data(b'x' * 50)
        if isinstance(result, np.ndarray):
            print("✓ Small data handling works")
        
        return True
    except Exception as e:
        print(f"✗ Error testing audio_utils: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_processor():
    """Test VoiceProcessor"""
    print("\n" + "=" * 60)
    print("4. Testing VoiceProcessor...")
    print("=" * 60)
    
    try:
        from voice_translation.core.processor import VoiceProcessor
        import numpy as np
        
        print("✓ Initializing VoiceProcessor...")
        processor = VoiceProcessor()
        print("✓ VoiceProcessor initialized")
        
        # Test with dummy audio
        dummy_audio = np.random.randn(16000).astype(np.float32) * 0.01
        text, lang = processor.transcribe_audio(dummy_audio)
        print(f"✓ Transcription test completed (result: '{text}', lang: {lang})")
        
        # Check translation models
        if processor.translation_models:
            print(f"✓ Translation models loaded: {list(processor.translation_models.keys())}")
        else:
            print("⚠ No translation models loaded")
        
        return True
    except Exception as e:
        print(f"✗ Error testing processor: {e}")
        import traceback
        traceback.print_exc()
        return False


def check_dependencies():
    """Check Python dependencies"""
    print("\n" + "=" * 60)
    print("5. Checking Python dependencies...")
    print("=" * 60)
    
    required = [
        'librosa',
        'numpy',
        'torch',
        'whisper',
        'transformers',
        'fastapi',
        'websockets'
    ]
    
    for package in required:
        try:
            __import__(package)
            print(f"✓ {package}")
        except ImportError:
            print(f"✗ {package} not installed")


def main():
    """Run all diagnostics"""
    print("\n" + "=" * 60)
    print("AUDIO PROCESSING PIPELINE DIAGNOSTICS")
    print("=" * 60)
    
    results = []
    
    results.append(("ffmpeg", check_ffmpeg()))
    test_webm_decode()
    results.append(("audio_utils", test_audio_utils()))
    results.append(("processor", test_processor()))
    check_dependencies()
    
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    
    for name, status in results:
        status_str = "✓ PASS" if status else "✗ FAIL"
        print(f"{name:20s} {status_str}")
    
    all_passed = all(status for _, status in results)
    
    if all_passed:
        print("\n✓ All critical tests passed!")
        print("\nYou can now test the WebSocket streaming:")
        print("  1. Start the server: python -m voice_translation.api")
        print("  2. Open browser: http://localhost:8000")
        print("  3. Click 'Start Streaming' and speak")
        return 0
    else:
        print("\n✗ Some tests failed. Please fix the issues above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
