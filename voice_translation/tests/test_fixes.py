#!/usr/bin/env python3
"""
Test script to verify the translation fixes
"""

import numpy as np

from voice_translation.core.audio_utils import load_audio_data
from voice_translation.core.processor import VoiceProcessor


def test_audio_loading():
    """Test audio loading with different scenarios"""
    print("Testing audio loading...")

    # Test with empty data
    empty_audio = load_audio_data(b"", sr=16000)
    print(f"Empty audio result: {len(empty_audio)} samples")

    # Test with small PCM data (simulated)
    sample_rate = 16000
    duration = 1.0  # 1 second
    frequency = 440  # A4 note

    # Generate sine wave
    t = np.linspace(0, duration, int(sample_rate * duration), False)
    sine_wave = np.sin(2 * np.pi * frequency * t)

    # Convert to 16-bit PCM bytes
    pcm_data = (sine_wave * 32767).astype(np.int16).tobytes()

    loaded_audio = load_audio_data(pcm_data, sr=16000)
    print(f"PCM audio loaded: {len(loaded_audio)} samples")

    return len(loaded_audio) > 0


def test_processor():
    """Test VoiceProcessor functionality"""
    print("Testing VoiceProcessor...")

    try:
        processor = VoiceProcessor()
        print("VoiceProcessor initialized successfully")

        # Test with empty audio
        empty_result = processor.transcribe_audio(np.array([]), language=None)
        print(f"Empty audio transcription: {empty_result}")

        # Test translation with empty text
        translation_result = processor.translate_text("", "en", "ar")
        print(f"Empty text translation: '{translation_result}'")

        # Test translation with same language
        same_lang_result = processor.translate_text("Hello", "en", "en")
        print(f"Same language translation: '{same_lang_result}'")

        return True
    except Exception as e:
        print(f"Processor test failed: {e}")
        return False


def main():
    """Run all tests"""
    print("Running translation system fixes test...\n")

    audio_test_passed = test_audio_loading()
    print(f"Audio loading test: {'PASSED' if audio_test_passed else 'FAILED'}\n")

    processor_test_passed = test_processor()
    print(f"Processor test: {'PASSED' if processor_test_passed else 'FAILED'}\n")

    if audio_test_passed and processor_test_passed:
        print("✅ All tests passed! The translation system fixes should work.")
    else:
        print("❌ Some tests failed. Please check the implementation.")


if __name__ == "__main__":
    main()
