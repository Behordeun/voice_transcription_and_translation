#!/usr/bin/env python3
import asyncio
import websockets
import json
import pyaudio
import base64

async def test_streaming():
    uri = "ws://localhost:8000/ws/transcribe-translate"
    
    print(f"Connecting to {uri}...")
    async with websockets.connect(uri) as ws:
        print("Connected!")
        
        # Send config
        config = {
            "type": "config",
            "source_language": None,
            "target_language": "ar"
        }
        await ws.send(json.dumps(config))
        print(f"Sent config: {config}")
        
        # Wait for config ack
        response = await ws.recv()
        print(f"Received: {response}")
        
        # Start audio capture
        CHUNK = 1024
        FORMAT = pyaudio.paInt16
        CHANNELS = 1
        RATE = 16000
        
        p = pyaudio.PyAudio()
        stream = p.open(format=FORMAT, channels=CHANNELS, rate=RATE, input=True, frames_per_buffer=CHUNK)
        
        print("Recording... (Press Ctrl+C to stop)")
        
        try:
            while True:
                # Read audio
                data = stream.read(CHUNK * 16)  # ~1 second
                b64_data = base64.b64encode(data).decode('utf-8')
                
                # Send chunk
                chunk_msg = {
                    "type": "chunk",
                    "encoding": "base64",
                    "data": b64_data
                }
                await ws.send(json.dumps(chunk_msg))
                print(f"Sent chunk: {len(data)} bytes")
                
                # Check for responses (non-blocking)
                try:
                    response = await asyncio.wait_for(ws.recv(), timeout=0.1)
                    print(f">>> {response}")
                except asyncio.TimeoutError:
                    pass
                    
        except KeyboardInterrupt:
            print("\nStopping...")
            await ws.send(json.dumps({"type": "flush"}))
            response = await ws.recv()
            print(f"Final: {response}")
            
        finally:
            stream.stop_stream()
            stream.close()
            p.terminate()

if __name__ == "__main__":
    asyncio.run(test_streaming())
