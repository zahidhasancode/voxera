"""Quick test script for streaming pipeline."""

import asyncio
import json
import websockets
from typing import Optional


async def test_websocket_streaming():
    """Test WebSocket streaming with audio frames."""
    uri = "ws://localhost:8000/api/v1/ws/"
    
    try:
        async with websockets.connect(uri) as websocket:
            print("✅ Connected to WebSocket")
            
            # Receive connection acknowledgment
            message = await websocket.recv()
            data = json.loads(message)
            print(f"📨 Received: {data}")
            
            # Send test audio frames (20ms PCM16 chunks)
            # Each frame is 320 bytes (20ms at 8kHz, 16-bit mono)
            frame_size = 320
            num_frames = 10
            
            print(f"\n📤 Sending {num_frames} audio frames...")
            for i in range(num_frames):
                # Generate mock audio frame (silence)
                frame = b"\x00" * frame_size
                await websocket.send(frame)
                print(f"  Frame {i+1}/{num_frames} sent ({len(frame)} bytes)")
                
                # Wait 20ms between frames (real-time simulation)
                await asyncio.sleep(0.02)
            
            print("\n✅ Test completed successfully!")
            print("Check server logs for queue stats and dispatcher activity")
            
    except Exception as e:
        print(f"❌ Error: {e}")


if __name__ == "__main__":
    print("🧪 Testing VOXERA Streaming Pipeline\n")
    print("Make sure the server is running: uvicorn app.main:app --reload\n")
    asyncio.run(test_websocket_streaming())
