## Quick orientation for AI code assistants

This repository implements a real-time voice transcription and translation system using FastAPI, Whisper, and MarianMT models. Use the guidance below to produce code, tests, and fixes that match repository conventions.

High-level pointers
- Main application lives in `voice_translation/` with FastAPI endpoints, WebSocket server, and ML processing.
- Primary workflows are docker-first. See `docker-compose.prod.yml` and `Dockerfile`. Typical commands: `docker compose -f docker-compose.prod.yml up -d`.
- Local development runs `python -m voice_translation.api` or `uv run python -m voice_translation.api`.

What to change and where
- HTTP endpoints: `voice_translation/api/main.py` - FastAPI routes for transcription, translation, and file upload.
- ML processing: `voice_translation/core/processor.py` - Whisper transcription and MarianMT translation logic.
- WebSocket server: `voice_translation/server/websocket_server.py` - Real-time audio streaming.
- Audio utilities: `voice_translation/core/audio_utils.py` and `voice_translation/core/audio.py`.
- Configuration: `.env.example` — runtime uses `.env`.

Tests & quality gates
- Tests: `test_*.py` files in root — run via `pytest`.
- Dependencies: `pyproject.toml` and `requirements.txt` for Docker builds.
- Formatting: `black` + `isort` as specified in `pyproject.toml`.

Conventions and idioms to preserve
- Type-first Python (3.11+). Add type annotations for public functions and return values.
- Structured logging via `voice_translation/core/error_trace.py` and `voice_translation/core/logging_config.py`.
- Lazy-load heavy ML models in `voice_translation/core/processor.py`: initialize once, cache Whisper and MarianMT models, use thread-safe loading.
- Performance optimizations: FP16 inference, pre-loading common models, minimal audio processing intervals.

Integration points and external dependencies
- Whisper (OpenAI) for speech-to-text transcription.
- MarianMT (Hugging Face) for text translation between English and Arabic.
- PyAudio for audio capture (optional, WebSocket-based streaming preferred).
- FastAPI for REST endpoints and static file serving.
- WebSockets for real-time audio streaming.

When writing code changes
- Keep small, self-contained changes with type hints.
- Test audio processing with sample files.
- Preserve API contracts in `voice_translation/api/main.py`.
- Update static UI in `voice_translation/static/index.html` if needed.
- Follow ML model patterns: lazy loading, error handling, caching.

Examples to reference when implementing changes
- Model loading patterns in `voice_translation/core/processor.py`.
- FastAPI endpoint structure in `voice_translation/api/main.py`.
- WebSocket handling in `voice_translation/server/websocket_server.py`.
- Audio processing utilities in `voice_translation/core/audio_utils.py`.

Quick checks before submitting code
- Test with sample audio files for transcription accuracy.
- Verify Docker build: `docker compose -f docker-compose.prod.yml build`.
- Check real-time performance with 2-second audio chunks.
- Ensure no secrets in diffs (.env files).

If anything is unclear
- Ask about deployment target: Docker vs local Python environment.
- Mention relevant files: `docker-compose.prod.yml`, `requirements.txt`, `voice_translation/api/main.py`.

End of instructions.
