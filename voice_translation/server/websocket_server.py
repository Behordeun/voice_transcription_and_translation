import asyncio
import json

import websockets

from ..core.audio import AudioCapture
from ..core.error_trace import logger
from ..core.processor import VoiceProcessor


class TranslationServer:
    def __init__(self, host="localhost", port=8765):
        self.host = host
        self.port = port
        logger.info("Initializing TranslationServer", {"host": host, "port": port})

        try:
            self.voice_processor = VoiceProcessor()
            self.audio_capture = AudioCapture()
            logger.info("TranslationServer components initialized successfully")
        except Exception as e:
            logger.error(e, {"component": "translation_server_init"}, exc_info=True)
            raise

        self.connected_users = {}
        self.user_preferences = {}

    async def register_user(self, websocket, user_data):
        user_id = user_data.get("user_id")
        preferred_language = user_data.get("preferred_language", "en")

        logger.info(
            "User registration request",
            {"user_id": user_id, "preferred_language": preferred_language},
        )

        self.connected_users[user_id] = websocket
        self.user_preferences[user_id] = preferred_language

        await websocket.send(
            json.dumps(
                {
                    "type": "registration_success",
                    "user_id": user_id,
                    "preferred_language": preferred_language,
                }
            )
        )

        logger.info(
            "User registered successfully",
            {"user_id": user_id, "total_connected_users": len(self.connected_users)},
        )

    async def handle_audio_processing(self):
        self.audio_capture.start_recording()
        last_processed_time = 0

        while True:
            current_time = asyncio.get_event_loop().time()

            # Process every 2 seconds for real-time performance
            if current_time - last_processed_time >= 2.0:
                audio_buffer = self.audio_capture.get_audio_buffer(duration_seconds=2)

                if (
                    len(audio_buffer) > 8000 and len(self.connected_users) > 0
                ):  # Min 0.5s audio
                    try:
                        results = self.voice_processor.process_multi_speaker_audio(
                            audio_buffer, self.user_preferences
                        )
                        if results:
                            await self.broadcast_results(results)
                    except Exception as e:
                        logger.error(e, {"component": "audio_processing"})

                last_processed_time = current_time

            await asyncio.sleep(0.1)  # Reduced sleep for better responsiveness

    async def broadcast_results(self, results):
        for speaker_id, data in results.items():
            message = {
                "type": "transcription_result",
                "speaker_id": speaker_id,
                "original_text": data["original_text"],
                "detected_language": data["detected_language"],
                "translations": data["translations"],
            }

            disconnected_users = []
            for user_id, websocket in self.connected_users.items():
                try:
                    await websocket.send(json.dumps(message))
                except websockets.exceptions.ConnectionClosed:
                    disconnected_users.append(user_id)

            for user_id in disconnected_users:
                logger.info("User disconnected", {"user_id": user_id})
                del self.connected_users[user_id]
                if user_id in self.user_preferences:
                    del self.user_preferences[user_id]

    async def handle_client(self, websocket):
        try:
            async for message in websocket:
                data = json.loads(message)

                if data["type"] == "register":
                    await self.register_user(websocket, data)
                elif data["type"] == "update_preference":
                    user_id = data["user_id"]
                    new_language = data["preferred_language"]
                    self.user_preferences[user_id] = new_language

        except websockets.exceptions.ConnectionClosed:
            logger.info("WebSocket connection closed")
        except Exception as e:
            logger.error(e, {"component": "websocket_handler"}, exc_info=True)

    async def start_server(self):
        _ = asyncio.create_task(self.handle_audio_processing())

        async with websockets.serve(self.handle_client, self.host, self.port):
            logger.info(
                "Translation server started", {"host": self.host, "port": self.port}
            )
            await asyncio.Future()

    def cleanup(self):
        logger.info("Cleaning up TranslationServer")
        try:
            self.audio_capture.cleanup()
            logger.info("TranslationServer cleanup completed")
        except Exception as e:
            logger.error(e, {"component": "cleanup"}, exc_info=True)
