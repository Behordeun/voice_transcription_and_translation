import os
from threading import Lock

import numpy as np
import torch
import whisper
from transformers import MarianMTModel, MarianTokenizer

from .error_trace import logger
import re


class VoiceProcessor:
    def __init__(self, hf_token=None):
        logger.info(
            "Initializing VoiceProcessor",
            {
                "hf_token_provided": bool(hf_token),
                "env_token_available": bool(os.getenv("HUGGINGFACE_TOKEN")),
            },
        )

        # Set device and optimize for inference
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        torch.set_num_threads(2)  # Limit CPU threads for better performance

        try:
            self.whisper_model = whisper.load_model("base", device=self.device)
            # Optimize Whisper for inference
            if hasattr(self.whisper_model, "eval"):
                self.whisper_model.eval()
            logger.info(f"Whisper model loaded on {self.device}")
        except Exception as e:
            logger.error(e, {"component": "whisper_model"}, exc_info=True)
            raise

        self.hf_token = hf_token or os.getenv("HUGGINGFACE_TOKEN")
        self.diarization_pipeline = None
        self.translation_models = {}
        self._model_lock = Lock()  # Thread safety for model loading

        # Pre-load common translation models
        self._preload_models()
        logger.info("VoiceProcessor initialization completed")

    def _preload_models(self):
        """Pre-load common translation models for better performance"""
        common_pairs = [("ar", "en"), ("en", "ar")]
        for src_lang, tgt_lang in common_pairs:
            self._load_single_translation_model(src_lang, tgt_lang)

    def _load_single_translation_model(self, src_lang, tgt_lang):
        """Load a single translation model with optimizations"""
        model_key = f"{src_lang}-{tgt_lang}"

        with self._model_lock:
            if model_key in self.translation_models:
                return

            # Only load supported language pairs
            supported_pairs = [("ar", "en"), ("en", "ar")]
            if (src_lang, tgt_lang) not in supported_pairs:
                print(f"WARNING: Unsupported language pair: {src_lang}-{tgt_lang}")
                return

            try:
                # Use better model names
                if src_lang == "en" and tgt_lang == "ar":
                    model_name = "Helsinki-NLP/opus-mt-en-ar"
                elif src_lang == "ar" and tgt_lang == "en":
                    model_name = "Helsinki-NLP/opus-mt-ar-en"
                else:
                    model_name = f"Helsinki-NLP/opus-mt-{src_lang}-{tgt_lang}"
                
                print(f"Loading translation model: {model_name}")
                tokenizer = MarianTokenizer.from_pretrained(model_name)
                model = MarianMTModel.from_pretrained(model_name)
                model.to(self.device)
                model.eval()
                self.translation_models[model_key] = (tokenizer, model)
                print(f"Successfully loaded translation model: {model_key}")
            except Exception as e:
                print(f"ERROR loading model {model_key}: {str(e)}")
                import traceback
                traceback.print_exc()

    def _load_diarization_pipeline(self):
        if self.hf_token:
            try:
                from pyannote.audio import Pipeline

                pipeline = Pipeline.from_pretrained(
                    "pyannote/speaker-diarization-3.1", token=self.hf_token
                )
                logger.info("Speaker diarization pipeline loaded successfully")
                return pipeline
            except Exception as e:
                logger.error(e, {"component": "speaker_diarization"})
        return None

    def separate_speakers(self, audio_data, sample_rate=16000):
        # Lazy load diarization pipeline
        if self.diarization_pipeline is None:
            self.diarization_pipeline = self._load_diarization_pipeline()

        if self.diarization_pipeline:
            try:
                diarization = self.diarization_pipeline(
                    {
                        "waveform": torch.tensor(audio_data).unsqueeze(0),
                        "sample_rate": sample_rate,
                    }
                )

                speakers = {}
                for turn, _, speaker in diarization.itertracks(yield_label=True):
                    if speaker not in speakers:
                        speakers[speaker] = []
                    start_sample = int(turn.start * sample_rate)
                    end_sample = int(turn.end * sample_rate)
                    speakers[speaker].append(audio_data[start_sample:end_sample])
                return speakers
            except Exception as e:
                logger.error(
                    e,
                    {
                        "component": "speaker_separation",
                        "audio_length": len(audio_data),
                    },
                )

        # Fallback to single speaker
        return {"speaker_0": [audio_data]}

    def _clean_transcription(self, text):
        """Clean transcription text by removing unwanted delimiters and artifacts"""
        if not text:
            return text
        
        # Remove multiple consecutive slashes (2 or more) with surrounding spaces
        # This handles: / /, / / /, / / / /, etc.
        text = re.sub(r'(\s*/\s*){2,}', ' ', text)
        
        # Remove multiple spaces
        text = re.sub(r'\s+', ' ', text)
        
        # Clean up spacing around punctuation
        text = re.sub(r'\s+([.,!?;:])', r'\1', text)
        
        return text.strip()

    def transcribe_audio(self, audio_data, language=None):
        try:
            # Quick validation
            if len(audio_data) == 0:
                return "", "unknown"

            # Ensure correct dtype and normalize
            audio_data = np.array(audio_data, dtype=np.float32)
            if np.max(np.abs(audio_data)) == 0:
                return "", "unknown"

            # Skip very short audio (< 0.5 seconds)
            if len(audio_data) < 8000:  # 16kHz * 0.5s
                return "", "unknown"

            # Optimized Whisper options for speed
            with torch.no_grad():
                result = self.whisper_model.transcribe(
                    audio_data,
                    language=language,
                    fp16=torch.cuda.is_available(),
                    no_speech_threshold=0.6,
                    logprob_threshold=-1.0,
                    compression_ratio_threshold=2.4,
                )

            text = result["text"].strip()
            text = self._clean_transcription(text)  # Clean the transcription
            detected_lang = result.get("language", "en")

            # Validate detected language
            valid_languages = {
                "en",
                "ar",
                "es",
                "fr",
                "de",
                "it",
                "pt",
                "ru",
                "ja",
                "ko",
                "zh",
                "hi",
            }
            if detected_lang not in valid_languages:
                detected_lang = "en"

            return text, detected_lang
        except Exception as e:
            logger.error(e, {"component": "transcription"}, exc_info=True)
            return "", "unknown"

    def translate_text(self, text, src_lang, tgt_lang):
        # Quick validation
        if not text or not text.strip() or src_lang == tgt_lang:
            return text

        model_key = f"{src_lang}-{tgt_lang}"

        if model_key not in self.translation_models:
            return text  # Skip if model not available

        try:
            tokenizer, model = self.translation_models[model_key]

            # Split long text into sentences for better translation
            sentences = text.replace('؟', '؟|').replace('?', '?|').replace('.', '.|').replace('!', '!|').split('|')
            sentences = [s.strip() for s in sentences if s.strip()]
            
            translated_parts = []
            for sentence in sentences:
                inputs = tokenizer(
                    sentence,
                    return_tensors="pt",
                    padding=True,
                    truncation=True,
                    max_length=512,
                ).to(self.device)

                with torch.no_grad():
                    outputs = model.generate(
                        **inputs,
                        max_length=512,
                        num_beams=4,
                        early_stopping=True,
                        pad_token_id=tokenizer.pad_token_id,
                    )

                translated = tokenizer.decode(outputs[0], skip_special_tokens=True).strip()
                if translated:
                    translated_parts.append(translated)

            return ' '.join(translated_parts) if translated_parts else text

        except Exception as e:
            logger.error(e, {"component": "translation"})
            return text

    def process_multi_speaker_audio(self, audio_data, user_preferences):
        if len(audio_data) == 0:
            return {}

        # Skip speaker separation for real-time performance
        text, detected_lang = self.transcribe_audio(audio_data)

        if not text.strip():
            return {}

        results = {
            "speaker_0": {
                "original_text": text,
                "detected_language": detected_lang,
                "translations": {},
            }
        }

        # Batch translations for efficiency
        for user_id, pref_lang in user_preferences.items():
            if detected_lang != pref_lang:
                translated = self.translate_text(text, detected_lang, pref_lang)
                results["speaker_0"]["translations"][user_id] = translated

        return results
