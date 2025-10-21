# Voice Translation and Transcription System

A real-time multi-speaker voice translation system supporting English, Arabic, Turkish, and Chinese languages.

## Features

- **Multi-speaker separation**: Automatically identifies and separates different speakers
- **Real-time transcription**: Uses Whisper for accurate speech-to-text
- **Multi-language translation**: Supports translation between EN, AR, TR, ZH
- **Multi-user support**: Multiple users can connect simultaneously with different language preferences
- **Real-time communication**: WebSocket-based for instant results

## Installation

```bash
# Install with UV (recommended)
uv sync

# Or install with pip
pip install -e .
```

## Usage

### FastAPI Server (Recommended)
```bash
# Start REST API server
uv run voice-api

# API will be available at http://localhost:8000
# Documentation at http://localhost:8000/docs
```

### WebSocket Server (Alternative)
```bash
# Start WebSocket server
uv run voice-server

# Connect GUI client
uv run voice-client
```

## System Architecture

- **VoiceProcessor**: Core engine for speaker separation, transcription, and translation
- **AudioCapture**: Real-time audio recording and buffering
- **TranslationServer**: WebSocket server managing multi-user connections
- **Client**: GUI application for users to connect and view results

## Supported Languages

- English (en)
- Arabic (ar)
- Turkish (tr)
- Chinese (zh)

## How It Works

1. System continuously captures audio from microphone
2. Speaker diarization separates different speakers
3. Each speaker's audio is transcribed using Whisper
4. Text is translated to each connected user's preferred language
5. Results are broadcast to all connected clients in real-time