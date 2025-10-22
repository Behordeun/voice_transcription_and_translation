# Deployment Instructions

## Rebuild and Deploy with Latest Changes

### Option 1: Using Docker Compose (Recommended)

```bash
cd /home/ubuntu/projects/voice_transcription_and_translation

# Stop and remove old container
docker-compose down

# Rebuild with latest changes
docker-compose build --no-cache

# Start the service
docker-compose up -d

# View logs
docker-compose logs -f
```

### Option 2: Using Docker Directly

```bash
cd /home/ubuntu/projects/voice_transcription_and_translation

# Stop and remove old container
docker stop voice-translation-api
docker rm voice-translation-api

# Rebuild image
docker build --no-cache -t voice-translation .

# Run new container
docker run -d \
  --name voice-translation-api \
  -p 8000:8000 \
  -p 8765:8765 \
  -v $(pwd)/logs:/app/logs \
  voice-translation

# View logs
docker logs -f voice-translation-api
```

## Verify Deployment

### Check Health

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

### Test Transcription

```bash
# Upload an audio file
curl -X POST http://localhost:8000/transcribe \
  -F "file=@your-audio.wav" \
  -F "target_language=ar"
```

## Latest Changes Applied

✅ Slash cleaning (removes / / / / patterns)
✅ Upgraded Whisper model (tiny → base)
✅ Optimized health checks (5s → 30s intervals)
✅ Enhanced health check with model validation
✅ Removed health check logging
✅ Increased translation token limits (256→512)
✅ Added soundfile package
