# Quick Start Guide

## Your WebSocket is Working! ✓

Your browser is successfully:
- Connecting to WebSocket
- Sending audio chunks (WebM/Opus format)
- Encoding to base64
- Transmitting ~16KB every second

## What Was Optimized

### 1. Audio Processing (`audio_utils.py`)
- Better WebM/Opus handling with ffmpeg
- Improved validation and error handling
- Faster processing with optimized settings

### 2. WebSocket Handler (`api/main.py`)
- Smarter buffering (45KB = ~3 seconds)
- Better interim result timing
- Cleaner buffer management
- Reduced log noise

### 3. Performance
- Audio processed in thread pool (non-blocking)
- Minimum 0.5s audio requirement
- Clear buffer after processing (prevents memory buildup)

## Install & Run (3 Steps)

```bash
# 1. Install dependencies
./install_dependencies.sh

# 2. Start server
source venv/bin/activate
uvicorn voice_translation.api.main:app --host 0.0.0.0 --port 8000 --reload

# 3. Test in browser
# Open: http://localhost:8000
# Click "Start Streaming" and speak
```

## Quick Test

```bash
# Check if everything is ready
python3 diagnose_audio.py

# Test WebSocket endpoint
python3 test_websocket_streaming.py
```

## Expected Behavior

### Browser Console
```
WebSocket connected ✓
Config acknowledged ✓
Microphone access granted ✓
Using codec: audio/webm;codecs=opus ✓
Sending audio chunks... ✓
```

### Server Response
```json
// After ~3 seconds of speech
{"type": "interim", "text": "hello world", "detected_language": "en"}

// After clicking stop or flush
{
  "type": "final",
  "original_text": "hello world",
  "translated_text": "مرحبا بالعالم",
  "detected_language": "en",
  "target_language": "ar"
}
```

## Troubleshooting

### Issue: "ffmpeg not found"
```bash
sudo apt-get install ffmpeg
```

### Issue: "No audio decoded"
- Check ffmpeg installed: `which ffmpeg`
- Verify browser codec: Check console for "Using codec:"
- Try Chrome/Firefox (better WebM support)

### Issue: "Empty transcription"
- Speak louder/clearer
- Wait for 3+ seconds of audio
- Check microphone permissions

### Issue: "Slow response"
Reduce buffer size in `api/main.py` line ~380:
```python
if len(self.buffer_bytes) >= 30000:  # 2 seconds instead of 3
```

## Configuration

### Change Target Language
In browser, select from dropdown before clicking "Start Streaming"

### Adjust Processing Interval
Edit `api/main.py`:
```python
# Line ~380 - Buffer threshold
if len(self.buffer_bytes) >= 45000:  # Adjust this value
    await self._maybe_send_interim()

# Smaller = faster but less accurate
# Larger = slower but more accurate
```

### Change Whisper Model
Edit `core/processor.py`:
```python
# Line ~28 - Model size
self.whisper_model = whisper.load_model("base", device=self.device)
# Options: tiny, base, small, medium, large
```

## Files Modified

1. `voice_translation/core/audio_utils.py` - Audio loading optimization
2. `voice_translation/api/main.py` - WebSocket handler improvements
3. `diagnose_audio.py` - New diagnostic tool
4. `test_websocket_streaming.py` - New test script
5. `install_dependencies.sh` - New installation script

## Next Steps

1. **Run installation**: `./install_dependencies.sh`
2. **Start server**: See "Install & Run" above
3. **Test streaming**: Open browser and try it
4. **Monitor logs**: Check `logs/` directory for issues
5. **Tune performance**: Adjust settings based on your needs

## Support

- Full guide: See `SETUP_GUIDE.md`
- Diagnostics: Run `python3 diagnose_audio.py`
- Health check: `curl http://localhost:8000/health`
- Logs: `tail -f logs/info.log`

---

**Your system is ready!** Just install dependencies and start the server.
