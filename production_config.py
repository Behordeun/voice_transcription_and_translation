"""Production configuration for optimized performance"""

import os

import torch

# Model optimization settings
WHISPER_MODEL_SIZE = "tiny"  # Fastest model
USE_GPU = torch.cuda.is_available()
TORCH_THREADS = 2  # Limit CPU threads
FP16_INFERENCE = USE_GPU  # Use FP16 only on GPU

# Audio processing settings
AUDIO_CHUNK_DURATION = 2.0  # Seconds
MIN_AUDIO_LENGTH = 0.5  # Minimum audio length to process
SAMPLE_RATE = 16000

# Translation settings
MAX_TRANSLATION_LENGTH = 32  # Tokens
TRANSLATION_TIMEOUT = 1.0  # Seconds

# Server settings
WEBSOCKET_PING_INTERVAL = 20
WEBSOCKET_PING_TIMEOUT = 10
MAX_CONCURRENT_REQUESTS = 10

# Caching
ENABLE_MODEL_CACHE = True
PRELOAD_TRANSLATION_MODELS = True

# Logging
LOG_LEVEL = "INFO" if os.getenv("PRODUCTION") else "DEBUG"
