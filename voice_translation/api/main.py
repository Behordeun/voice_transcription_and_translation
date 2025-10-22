from dotenv import load_dotenv
from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from ..core.audio_utils import load_audio_data
from ..core.error_trace import logger
from ..core.processor import VoiceProcessor

load_dotenv()

app = FastAPI(title="Voice Translation API", version="1.0.0")
logger.info("Starting Voice Translation API", {"version": "1.0.0"})

try:
    processor = VoiceProcessor()
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
    """Health check endpoint"""
    logger.debug("Health check requested")
    return {"status": "healthy", "service": "voice-translation-api"}


@app.get("/languages")
async def get_supported_languages():
    """Get supported languages"""
    return {"supported_languages": {"en": "English", "ar": "Arabic"}}
