import queue
import threading
import time

import numpy as np
import pyaudio

from .error_trace import logger


class AudioCapture:
    def __init__(self, sample_rate=16000, chunk_size=1024, channels=1):
        logger.info(
            "Initializing AudioCapture",
            {
                "sample_rate": sample_rate,
                "chunk_size": chunk_size,
                "channels": channels,
            },
        )

        self.sample_rate = sample_rate
        self.chunk_size = chunk_size
        self.channels = channels
        self.audio_queue = queue.Queue()
        self.is_recording = False
        self.audio_thread = None

        try:
            self.audio = pyaudio.PyAudio()
            logger.info("PyAudio initialized successfully")
        except Exception as e:
            logger.error(e, {"component": "pyaudio_init"}, exc_info=True)
            raise

    def start_recording(self):
        logger.info("Starting audio recording")
        try:
            self.is_recording = True
            self.audio_thread = threading.Thread(target=self._record_audio)
            self.audio_thread.start()
            logger.info("Audio recording started successfully")
        except Exception as e:
            logger.error(e, {"component": "start_recording"}, exc_info=True)
            raise

    def stop_recording(self):
        logger.info("Stopping audio recording")
        try:
            self.is_recording = False
            if self.audio_thread:
                self.audio_thread.join()
            logger.info("Audio recording stopped successfully")
        except Exception as e:
            logger.error(e, {"component": "stop_recording"}, exc_info=True)

    def _record_audio(self):
        stream = self.audio.open(
            format=pyaudio.paFloat32,
            channels=self.channels,
            rate=self.sample_rate,
            input=True,
            frames_per_buffer=self.chunk_size,
        )

        try:
            logger.debug("Audio recording loop started")
            while self.is_recording:
                data = stream.read(self.chunk_size, exception_on_overflow=False)
                audio_data = np.frombuffer(data, dtype=np.float32)
                self.audio_queue.put(audio_data)
        except Exception as e:
            logger.error(e, {"component": "audio_recording_loop"}, exc_info=True)
        finally:
            stream.stop_stream()
            stream.close()
            logger.debug("Audio stream closed")

    def get_audio_chunk(self, timeout=1):
        try:
            return self.audio_queue.get(timeout=timeout)
        except queue.Empty:
            return None

    def get_audio_buffer(self, duration_seconds=5):
        buffer = []
        start_time = time.time()

        while time.time() - start_time < duration_seconds:
            chunk = self.get_audio_chunk(timeout=0.1)
            if chunk is not None:
                buffer.append(chunk)

        return np.concatenate(buffer) if buffer else np.array([])

    def cleanup(self):
        logger.info("Cleaning up AudioCapture")
        try:
            self.stop_recording()
            self.audio.terminate()
            logger.info("AudioCapture cleanup completed")
        except Exception as e:
            logger.error(e, {"component": "audio_cleanup"}, exc_info=True)
