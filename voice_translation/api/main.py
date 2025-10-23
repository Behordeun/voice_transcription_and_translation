from dotenv import load_dotenv
from fastapi import FastAPI, File, Form, HTTPException, UploadFile, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from ..core.audio_utils import load_audio_data
from ..core.error_trace import logger
from ..core.processor import VoiceProcessor
from .security import SecurityMiddleware
import json
import base64
import numpy as np
import asyncio
from concurrent.futures import ThreadPoolExecutor

load_dotenv()

app = FastAPI(title="Voice Translation API", version="1.0.0")
app.add_middleware(SecurityMiddleware)
logger.info("Starting Voice Translation API", {"version": "1.0.0"})

try:
    processor = VoiceProcessor()
    executor = ThreadPoolExecutor(max_workers=4)
    logger.info("VoiceProcessor initialized successfully")
except Exception as e:
    logger.error(e, {"component": "processor_initialization"}, exc_info=True)
    raise

# Mount static files
import os
static_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "static")
app.mount("/static", StaticFiles(directory=static_dir), name="static")


@app.post("/transcribe")
async def transcribe_audio(
    file: UploadFile = File(...),
    language: str = Form(None),
    target_language: str = Form(None),
):
    """Transcribe audio file with optional target language translation"""
    logger.info(
        "Transcription request received",
        {
            "filename": file.filename,
            "content_type": file.content_type,
            "language": language,
            "target_language": target_language,
        },
    )

    try:
        audio_data = await file.read()
        audio_array = load_audio_data(audio_data, sr=16000)

        text, detected_lang = processor.transcribe_audio(audio_array, language)

        # Translate if target language is specified and different from detected
        if target_language and detected_lang != target_language and text.strip():
            text = processor.translate_text(text, detected_lang, target_language)

        logger.info(
            "Transcription completed successfully",
            {
                "detected_language": detected_lang,
                "target_language": target_language,
                "text_length": len(text),
            },
        )

        return {
            "text": text,
            "detected_language": detected_lang,
            "target_language": target_language or detected_lang,
            "status": "success",
        }
    except Exception as e:
        logger.error(
            e,
            {
                "endpoint": "/transcribe",
                "filename": file.filename,
                "language": language,
                "target_language": target_language,
            },
            exc_info=True,
        )
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/transcribe-translate")
async def transcribe_and_translate(
    file: UploadFile = File(...),
    target_language: str = Form(...),
    source_language: str = Form(None),
):
    """Transcribe audio and translate to target language"""
    logger.info(
        "Transcribe-translate request received",
        {
            "filename": file.filename,
            "target_language": target_language,
            "source_language": source_language,
        },
    )

    try:
        audio_data = await file.read()

        # Validate audio data
        if not audio_data or len(audio_data) < 100:  # Minimum reasonable audio size
            raise HTTPException(
                status_code=400, detail="Audio file is empty or too small"
            )

        audio_array = load_audio_data(audio_data, sr=16000)

        # Validate loaded audio
        if len(audio_array) == 0:
            raise HTTPException(
                status_code=400,
                detail="Failed to load audio data - unsupported format or corrupted file",
            )

        text, detected_lang = processor.transcribe_audio(audio_array, source_language)

        # Validate transcription result
        if not text or not text.strip():
            logger.warning("No text transcribed from audio")
            return {
                "original_text": "",
                "translated_text": "",
                "detected_language": detected_lang,
                "target_language": target_language,
                "status": "success",
                "message": "No speech detected in audio",
            }

        # Translate if target language is different from detected language
        translated_text = text
        if detected_lang != target_language and text.strip():
            translated_text = processor.translate_text(
                text, detected_lang, target_language
            )

        logger.info(
            "Transcribe-translate completed successfully",
            {
                "detected_language": detected_lang,
                "target_language": target_language,
                "translation_needed": detected_lang != target_language,
            },
        )

        return {
            "original_text": text,
            "translated_text": translated_text,
            "detected_language": detected_lang,
            "target_language": target_language,
            "status": "success",
        }
    except Exception as e:
        logger.error(
            e,
            {
                "endpoint": "/transcribe-translate",
                "filename": file.filename,
                "target_language": target_language,
                "source_language": source_language,
            },
            exc_info=True,
        )
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/translate")
async def translate_text(
    text: str = Form(...),
    source_language: str = Form(...),
    target_language: str = Form(...),
):
    """Translate text between languages"""
    logger.info(
        "Text translation request received",
        {
            "text": text[:50] + "..." if len(text) > 50 else text,
            "source_language": source_language,
            "target_language": target_language,
        },
    )

    # Validate input
    if not text or not text.strip():
        raise HTTPException(status_code=400, detail="Text cannot be empty")

    if source_language not in ["en", "ar"]:
        raise HTTPException(status_code=400, detail="Unsupported source language")

    if target_language not in ["en", "ar"]:
        raise HTTPException(status_code=400, detail="Unsupported target language")

    try:
        translated = processor.translate_text(
            text.strip(), source_language, target_language
        )

        logger.info(
            "Text translation completed successfully",
            {
                "source_language": source_language,
                "target_language": target_language,
                "original_length": len(text),
                "translated_length": len(translated),
            },
        )

        return {
            "original_text": text.strip(),
            "translated_text": translated,
            "source_language": source_language,
            "target_language": target_language,
            "status": "success",
        }
    except Exception as e:
        logger.error(
            e,
            {
                "endpoint": "/translate",
                "source_language": source_language,
                "target_language": target_language,
                "text_length": len(text),
            },
            exc_info=True,
        )
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/process-multi-speaker")
async def process_multi_speaker(
    file: UploadFile = File(...),
    user_preferences: str = Form(...),  # JSON string: {"user1": "en", "user2": "ar"}
):
    """Process multi-speaker audio with translation"""
    logger.info(
        "Multi-speaker processing request received",
        {"filename": file.filename, "user_preferences": user_preferences},
    )

    try:
        import json

        audio_data = await file.read()
        audio_array = load_audio_data(audio_data, sr=16000)

        preferences = json.loads(user_preferences)
        results = processor.process_multi_speaker_audio(audio_array, preferences)

        logger.info(
            "Multi-speaker processing completed successfully",
            {"speakers_detected": len(results), "user_preferences": preferences},
        )

        return {"results": results, "status": "success"}
    except Exception as e:
        logger.error(
            e,
            {
                "endpoint": "/process-multi-speaker",
                "filename": file.filename,
                "user_preferences": user_preferences,
            },
            exc_info=True,
        )
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/")
async def root():
    """Serve the main UI page"""
    index_path = os.path.join(static_dir, "index.html")
    return FileResponse(index_path)


@app.get("/health")
async def health_check():
    """Health check endpoint with model validation"""
    try:
        # Check if Whisper model is loaded
        if not hasattr(processor, 'whisper_model') or processor.whisper_model is None:
            return JSONResponse(
                status_code=503,
                content={"status": "unhealthy", "reason": "whisper_model_not_loaded"}
            )
        
        # Check if translation models are loaded
        if not processor.translation_models:
            return JSONResponse(
                status_code=503,
                content={"status": "unhealthy", "reason": "translation_models_not_loaded"}
            )
        
        return {
            "status": "healthy",
            "service": "voice-translation-api",
            "models": {
                "whisper": "loaded",
                "translation_pairs": list(processor.translation_models.keys())
            }
        }
    except Exception:
        return JSONResponse(
            status_code=503,
            content={"status": "unhealthy", "reason": "internal_error"}
        )


@app.get("/languages")
async def get_supported_languages():
    """Get supported languages"""
    return {"supported_languages": {"en": "English", "ar": "Arabic"}}


class _WSHandler:
    def __init__(self, websocket):
        self.websocket = websocket
        self.buffer_bytes = bytearray()
        self.config = {"source_language": None, "target_language": None}

    async def accept(self):
        await self.websocket.accept()

    async def send_json(self, obj):
        await self.websocket.send_text(json.dumps(obj))

    async def handle_config(self, data):
        self.config["source_language"] = data.get("source_language")
        self.config["target_language"] = data.get("target_language")
        await self.send_json({"type": "config_ack", "config": self.config})

    async def handle_chunk(self, data):
        enc = data.get("encoding", "base64")
        if enc != "base64":
            await self.send_json({"type": "error", "detail": "unsupported_encoding"})
            return

        chunk_b64 = data.get("data")
        if not chunk_b64:
            return

        try:
            chunk = base64.b64decode(chunk_b64)
            logger.debug(f"Received chunk: {len(chunk)} bytes, buffer: {len(self.buffer_bytes)} bytes")
        except Exception:
            await self.send_json({"type": "error", "detail": "invalid_base64"})
            return

        self.buffer_bytes.extend(chunk)
        # Process every 3 chunks (~3 seconds) for better accuracy
        if len(self.buffer_bytes) >= 45000:
            await self._maybe_send_interim()

    async def _maybe_send_interim(self):
        try:
            # Run audio loading in thread pool
            loop = asyncio.get_event_loop()
            audio_array = await loop.run_in_executor(executor, load_audio_data, bytes(self.buffer_bytes), 16000)
            
            if audio_array is None or len(audio_array) == 0:
                logger.debug(f"No audio decoded from {len(self.buffer_bytes)} bytes buffer")
                return
            
            # Skip if audio too short (< 0.5s)
            if len(audio_array) < 8000:
                logger.debug(f"Audio too short: {len(audio_array)} samples")
                return
            
            # Run transcription in thread pool
            text, detected = await loop.run_in_executor(
                executor, 
                processor.transcribe_audio, 
                audio_array, 
                self.config.get("source_language")
            )
            
            if text and text.strip():
                await self.send_json({"type": "interim", "text": text, "detected_language": detected})
                logger.info(f"Interim result: {text[:50]}...")
        except Exception as e:
            logger.error(f"Error in interim processing: {e}", exc_info=True)
        finally:
            # Clear buffer after processing to avoid memory buildup
            self.buffer_bytes.clear()

    async def handle_flush(self):
        try:
            loop = asyncio.get_event_loop()
            audio_array = await loop.run_in_executor(executor, load_audio_data, bytes(self.buffer_bytes), 16000)
            
            if audio_array is None or len(audio_array) == 0:
                await self.send_json({
                    "type": "final",
                    "original_text": "",
                    "translated_text": "",
                    "detected_language": "unknown",
                    "target_language": self.config.get("target_language")
                })
                self.buffer_bytes.clear()
                return

            text, detected = await loop.run_in_executor(
                executor,
                processor.transcribe_audio,
                audio_array,
                self.config.get("source_language")
            )
            
            translated_text = text
            tgt = self.config.get("target_language")
            if tgt and detected != tgt and text.strip():
                translated_text = await loop.run_in_executor(
                    executor,
                    processor.translate_text,
                    text,
                    detected,
                    tgt
                )

            await self.send_json({
                "type": "final",
                "original_text": text,
                "translated_text": translated_text,
                "detected_language": detected,
                "target_language": tgt,
            })
        except Exception as e:
            logger.error(f"Error in flush processing: {e}", exc_info=True)
            await self.send_json({"type": "error", "detail": str(e)})
        finally:
            self.buffer_bytes.clear()

    async def process_text_message(self, msg: str):
        """Parse incoming text message and dispatch to appropriate handler.
           Returns 'closed' when client requested close, otherwise None."""
        try:
            data = json.loads(msg)
        except Exception:
            await self.send_json({"type": "error", "detail": "invalid_json"})
            return

        mtype = data.get("type")
        if mtype == "config":
            await self.handle_config(data)
        elif mtype == "chunk":
            await self.handle_chunk(data)
        elif mtype == "flush":
            await self.handle_flush()
        elif mtype == "close":
            # close and signal caller to stop loop
            await self.websocket.close()
            return "closed"
        else:
            await self.send_json({"type": "error", "detail": "unknown_message_type"})


@app.websocket("/ws/transcribe-translate")
async def websocket_transcribe_translate(websocket: WebSocket):
    """WebSocket endpoint for real-time streaming transcription + translation.

    Protocol (JSON messages):
    - Client -> Server:
      {"type": "config", "source_language": "en"}  # optional
      {"type": "chunk", "encoding": "base64", "data": "..."}  # audio bytes (wav or raw PCM)
      {"type": "flush"}  # ask server to process buffered audio immediately
      {"type": "close"}  # close the socket gracefully

    - Server -> Client:
      {"type": "interim", "text": "partial transcription", "detected_language": "en"}
      {"type": "final", "original_text": "...", "translated_text": "...", "detected_language": "en", "target_language": "ar"}
    """
    handler = _WSHandler(websocket)
    await handler.accept()

    try:
        while True:
            msg = await websocket.receive_text()
            result = await handler.process_text_message(msg)
            if result == "closed":
                return

    except WebSocketDisconnect:
        logger.info("WebSocket client disconnected")
    except Exception as e:
        logger.error(e, {"component": "ws_transcribe_translate"}, exc_info=True)
        try:
            await websocket.send_text(json.dumps({"type": "error", "detail": str(e)}))
        except Exception:
            pass
