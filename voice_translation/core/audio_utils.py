import io
import os
import tempfile

import librosa
import numpy as np

from .error_trace import logger


def load_audio_data(audio_data: bytes, sr: int = 16000) -> np.ndarray:
    """
    Load audio data from bytes with fallback mechanisms.

    Args:
        audio_data: Raw audio bytes
        sr: Target sample rate

    Returns:
        Audio array as numpy array
    """
    try:
        # Try direct BytesIO loading first
        audio_array, _ = librosa.load(io.BytesIO(audio_data), sr=sr)
        logger.debug("Audio loaded successfully via BytesIO")
        return audio_array
    except Exception as e:
        logger.warning("BytesIO loading failed, trying temp file", {"error": str(e)})

        # Fallback: write to temp file and load
        try:
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_file:
                temp_file.write(audio_data)
                temp_file.flush()
                temp_path = temp_file.name

            try:
                audio_array, _ = librosa.load(temp_path, sr=sr)
                logger.debug("Audio loaded successfully via temp file")
                return audio_array
            except Exception:
                # Final fallback: handle raw PCM data
                logger.warning("Temp file loading failed, trying raw PCM conversion")

                # Ensure buffer size is aligned for int16
                buffer_size = len(audio_data)
                if buffer_size % 2 != 0:
                    # Pad with zero byte if odd length
                    audio_data = audio_data + b"\x00"
                    buffer_size = len(audio_data)

                if buffer_size >= 2:
                    # Convert to 16-bit PCM and normalize to float32
                    audio_array = (
                        np.frombuffer(audio_data, dtype=np.int16).astype(np.float32)
                        / 32768.0
                    )

                    # Resample if needed
                    if sr != 16000:  # Assume original is 16kHz
                        audio_array = librosa.resample(
                            audio_array, orig_sr=16000, target_sr=sr
                        )

                    logger.debug(
                        "Audio converted from raw PCM", {"length": len(audio_array)}
                    )
                    return audio_array
                else:
                    logger.warning("Audio data too small", {"size": buffer_size})
                    return np.array([], dtype=np.float32)
            finally:
                # Clean up temp file
                try:
                    os.unlink(temp_path)
                except:
                    pass

        except Exception as raw_error:
            logger.error(raw_error, {"component": "audio_loading"}, exc_info=True)
            # Return empty array as last resort
            return np.array([], dtype=np.float32)
