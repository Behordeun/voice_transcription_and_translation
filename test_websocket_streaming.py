#!/usr/bin/env python3
"""Test WebSocket streaming with audio chunks"""

import asyncio
import json
import base64
import websockets
from pathlib import Path


async def test_streaming():
    """Test WebSocket streaming endpoint"""
    uri = "ws://localhost:8000/ws/transcribe-translate"
    
    print(f"Connecting to {uri}...")
    
    async with websockets.connect(uri) as websocket:
        print("✓ Connected")
        
        # Send config
        config = {
            "type": "config",
            "source_language": None,  # Auto-detect
            "target_language": "ar"
        }
        await websocket.send(json.dumps(config))
        print(f"✓ Sent config: {config}")
        
        # Wait for config acknowledgment
        response = await websocket.recv()
        data = json.loads(response)
        print(f"✓ Received: {data}")
        
        # Simulate sending audio chunks
        # In real scenario, these would be actual WebM/Opus audio chunks
        test_audio_file = Path(__file__).parent / "test_audio.wav"
        
        if test_audio_file.exists():
            print(f"\n✓ Found test audio file: {test_audio_file}")
            
            # Read and send in chunks
            with open(test_audio_file, "rb") as f:
                audio_data = f.read()
            
            # Send in 16KB chunks (simulating browser behavior)
            chunk_size = 16438
            for i in range(0, len(audio_data), chunk_size):
                chunk = audio_data[i:i+chunk_size]
                chunk_b64 = base64.b64encode(chunk).decode('utf-8')
                
                message = {
                    "type": "chunk",
                    "encoding": "base64",
                    "data": chunk_b64
                }
                await websocket.send(json.dumps(message))
                print(f"✓ Sent chunk {i//chunk_size + 1}: {len(chunk)} bytes")
                
                # Check for interim results
                try:
                    response = await asyncio.wait_for(websocket.recv(), timeout=0.1)
                    data = json.loads(response)
                    print(f"  → Interim: {data}")
                except asyncio.TimeoutError:
                    pass
                
                await asyncio.sleep(0.1)
            
            # Send flush to get final result
            await websocket.send(json.dumps({"type": "flush"}))
            print("\n✓ Sent flush")
            
            # Wait for final result
            response = await websocket.recv()
            data = json.loads(response)
            print(f"\n✓ Final result:")
            print(f"  Original: {data.get('original_text', '')}")
            print(f"  Translated: {data.get('translated_text', '')}")
            print(f"  Language: {data.get('detected_language', '')} → {data.get('target_language', '')}")
        else:
            print(f"\n⚠ No test audio file found at {test_audio_file}")
            print("  Create a test_audio.wav file or use the browser interface")
        
        # Close connection
        await websocket.send(json.dumps({"type": "close"}))
        print("\n✓ Connection closed")


if __name__ == "__main__":
    try:
        asyncio.run(test_streaming())
    except KeyboardInterrupt:
        print("\n\n✗ Interrupted by user")
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
