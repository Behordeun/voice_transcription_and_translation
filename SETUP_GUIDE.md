# WebSocket Audio Streaming Setup Guide

## Overview
Your WebSocket is successfully receiving audio chunks from the browser (WebM/Opus format). The optimizations made will improve the audio processing pipeline.

## Changes Made

### 1. Optimized `audio_utils.py`
- Added validation for minimum audio data size
- Improved ffmpeg command with error suppression (`-loglevel error`)
- Added check for valid WAV output (> 44 bytes header)
- Better error handling and logging

### 2. Optimized WebSocket Handler (`api/main.py`)
- Changed buffer threshold from 8KB to 45KB (~3 seconds of audio)
- Improved interim processing with better error handling
- Changed buffer strategy: clear after processing instead of sliding window
- Reduced log verbosity (debug instead of info for chunks)
- Added audio length validation before transcription

### 3. Created Diagnostic Tools
- `diagnose_audio.py`: Check entire pipeline health
- `test_websocket_streaming.py`: Test WebSocket endpoint

## Installation Steps

### 1. Install System Dependencies
```bash
# Install ffmpeg (required for WebM/Opus decoding)
sudo apt-get update
sudo apt-get install -y ffmpeg

# Verify installation
ffmpeg -version
```

### 2. Install Python Dependencies
```bash
# Create virtual environment (if not exists)
python3 -m venv venv
source venv/bin/activate

# Install requirements
pip install -r requirements.txt
```

### 3. Verify Setup
```bash
# Run diagnostics
python3 diagnose_audio.py

# Should show all tests passing
```

## Running the Application

### Start the Server
```bash
# Option 1: Using uvicorn directly
uvicorn voice_translation.api.main:app --host 0.0.0.0 --port 8000 --reload

# Option 2: Using the API module
python3 -m voice_translation.api

# Option 3: Using run_local.py (if available)
python3 run_local.py
```

### Test WebSocket Streaming

#### Browser Test (Recommended)
1. Open browser: `http://localhost:8000`
2. Select target language (e.g., Arabic)
3. Click "Start Streaming"
4. Allow microphone access
5. Speak into microphone
6. Watch for interim and final results

#### Command Line Test
```bash
python3 test_websocket_streaming.py
```

## How It Works

### Browser → Server Flow
1. **Browser captures audio**: MediaRecorder with WebM/Opus codec
2. **Chunks sent every 1 second**: ~16KB per chunk
3. **Server buffers chunks**: Accumulates until 45KB (~3 seconds)
4. **ffmpeg decodes WebM**: Converts to WAV format
5. **Whisper transcribes**: Converts speech to text
6. **Translation (optional)**: Translates to target language
7. **Results sent back**: Interim results during streaming, final on flush

### WebSocket Protocol

#### Client → Server Messages
```json
// 1. Configure session
{"type": "config", "source_language": null, "target_language": "ar"}

// 2. Send audio chunks
{"type": "chunk", "encoding": "base64", "data": "<base64_audio>"}

// 3. Request final processing
{"type": "flush"}

// 4. Close connection
{"type": "close"}
```

#### Server → Client Messages
```json
// Config acknowledgment
{"type": "config_ack", "config": {...}}

// Interim results (during streaming)
{"type": "interim", "text": "...", "detected_language": "en"}

// Final results (after flush)
{
  "type": "final",
  "original_text": "...",
  "translated_text": "...",
  "detected_language": "en",
  "target_language": "ar"
}

// Errors
{"type": "error", "detail": "error message"}
```

## Performance Tuning

### Current Settings
- **Buffer threshold**: 45KB (~3 seconds of audio)
- **Minimum audio length**: 0.5 seconds (8000 samples at 16kHz)
- **ffmpeg timeout**: 10 seconds
- **Thread pool workers**: 4

### Adjust for Your Needs

#### Lower Latency (faster but less accurate)
```python
# In api/main.py, line ~380
if len(self.buffer_bytes) >= 30000:  # ~2 seconds
    await self._maybe_send_interim()
```

#### Higher Accuracy (slower but better results)
```python
# In api/main.py, line ~380
if len(self.buffer_bytes) >= 60000:  # ~4 seconds
    await self._maybe_send_interim()
```

## Troubleshooting

### No Audio Decoded
**Symptom**: Logs show "No audio decoded from X bytes buffer"

**Solutions**:
1. Check ffmpeg is installed: `which ffmpeg`
2. Test ffmpeg manually:
   ```bash
   ffmpeg -i test.webm -ar 16000 -ac 1 -f wav output.wav
   ```
3. Check browser codec: Look for "Using codec:" in browser console
4. Try different browser (Chrome/Firefox have better WebM support)

### Empty Transcriptions
**Symptom**: Audio decoded but no text returned

**Solutions**:
1. Check audio is long enough (> 0.5 seconds)
2. Verify microphone is working
3. Check Whisper model loaded: `curl http://localhost:8000/health`
4. Increase buffer size for longer audio segments

### High Latency
**Symptom**: Slow response times

**Solutions**:
1. Reduce buffer threshold (see Performance Tuning)
2. Use GPU if available (check `processor.device`)
3. Reduce thread pool workers if CPU limited
4. Use smaller Whisper model (currently "base")

### Translation Not Working
**Symptom**: Original text shown but no translation

**Solutions**:
1. Check translation models loaded: `curl http://localhost:8000/health`
2. Verify language pair supported (currently: en↔ar)
3. Check logs for translation errors
4. Ensure detected language differs from target language

## Monitoring

### Check Server Health
```bash
curl http://localhost:8000/health
```

Expected response:
```json
{
  "status": "healthy",
  "service": "voice-translation-api",
  "models": {
    "whisper": "loaded",
    "translation_pairs": ["ar-en", "en-ar"]
  }
}
```

### View Logs
```bash
# Real-time logs
tail -f logs/info.log

# Error logs
tail -f logs/error.log

# Debug logs
tail -f logs/debug.log
```

## Browser Console Debugging

### Expected Console Output
```
WebSocket connected
Sending config: {type: 'config', source_language: null, target_language: 'ar'}
Requesting microphone access...
Received: {"type": "config_ack", "config": {...}}
Config acknowledged: {source_language: null, target_language: 'ar'}
Microphone access granted
Using codec: audio/webm;codecs=opus
MediaRecorder created
MediaRecorder started
ondataavailable fired, size: 14652
Sending audio chunk: 14652 bytes
Base64 length: 19536
...
Received: {"type": "interim", "text": "hello", "detected_language": "en"}
```

### Common Browser Issues

**No microphone access**:
- Check browser permissions
- Use HTTPS in production (required for getUserMedia)
- Try different browser

**No codec supported**:
- Browser doesn't support WebM/Opus
- Fallback to default codec (check console)
- May need different audio format

## Next Steps

1. **Install dependencies** (see Installation Steps above)
2. **Run diagnostics** to verify setup
3. **Start server** and test in browser
4. **Monitor logs** for any issues
5. **Adjust settings** based on your needs

## Support

If issues persist:
1. Check logs in `logs/` directory
2. Run `python3 diagnose_audio.py` for detailed diagnostics
3. Verify all dependencies installed
4. Check ffmpeg supports Opus codec: `ffmpeg -codecs | grep opus`
