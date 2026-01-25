# How to Check and Test the Streaming Pipeline

## 1. Quick Server Check

### Start the server:
```bash
uvicorn app.main:app --reload
```

### Expected output:
```
INFO:     Uvicorn running on http://127.0.0.1:8000
INFO:     Application startup complete.
```

If you see this, the server started successfully! ✅

## 2. Test WebSocket Connection

### Option A: Using the test script

```bash
# Make sure server is running first
python test_streaming.py
```

This will:
- Connect to WebSocket
- Send 10 test audio frames
- Show connection status

### Option B: Using Python interactively

```python
import asyncio
import websockets
import json

async def test():
    uri = "ws://localhost:8000/api/v1/ws/"
    async with websockets.connect(uri) as ws:
        # Receive connection message
        msg = await ws.recv()
        print(f"Received: {json.loads(msg)}")
        
        # Send audio frame (320 bytes = 20ms PCM16)
        frame = b"\x00" * 320
        await ws.send(frame)
        print("Frame sent!")

asyncio.run(test())
```

### Option C: Using curl (for HTTP endpoints)

```bash
# Test health endpoint
curl http://localhost:8000/api/v1/health

# Expected: {"status":"healthy","version":"0.1.0"}
```

## 3. Check Server Logs

When you send frames, you should see logs like:

```json
{
  "level": "INFO",
  "message": "WebSocket connection established with streaming pipeline",
  "queue_max_size": 50
}
```

```json
{
  "level": "DEBUG",
  "message": "Audio queue stats",
  "queue_depth": 5,
  "frames_enqueued": 100,
  "frames_dropped": 0
}
```

## 4. Verify Components

### Check imports work:
```bash
python -c "from app.streaming import AudioFrameQueue, StreamingDispatcher; print('✅ Imports OK')"
```

### Check server imports:
```bash
python -c "from app.main import app; print('✅ Server imports OK')"
```

## 5. Monitor Queue Behavior

### Test queue overflow (drop-oldest):
Send frames faster than 20ms to fill the queue:

```python
import asyncio
import websockets

async def test_overflow():
    uri = "ws://localhost:8000/api/v1/ws/"
    async with websockets.connect(uri) as ws:
        # Send 100 frames rapidly (should trigger drop-oldest)
        for i in range(100):
            await ws.send(b"\x00" * 320)
            await asyncio.sleep(0.001)  # 1ms delay (faster than 20ms)
        
        print("Sent 100 frames rapidly - check logs for dropped frames")

asyncio.run(test_overflow())
```

## 6. Check for Errors

### Common issues:

1. **Import errors:**
   ```bash
   python -m py_compile app/streaming/*.py
   ```

2. **Type errors:**
   ```bash
   # If you have mypy installed
   mypy app/streaming/
   ```

3. **Linter errors:**
   ```bash
   ruff check app/streaming/
   ```

## 7. Expected Behavior

✅ **Working correctly if:**
- Server starts without errors
- WebSocket accepts connections
- Frames are enqueued (check logs)
- Dispatcher runs (check logs for "Streaming dispatcher started")
- Queue stats are logged periodically
- No errors in server logs

❌ **Issues if:**
- `AttributeError: module 'asyncio' has no attribute 'coroutine'` → Already fixed!
- Connection refused → Server not running
- Import errors → Check Python path and dependencies

## 8. Quick Verification Checklist

- [ ] Server starts: `uvicorn app.main:app --reload`
- [ ] No import errors in terminal
- [ ] WebSocket connects: `python test_streaming.py`
- [ ] Logs show "Streaming dispatcher started"
- [ ] Logs show queue stats
- [ ] No errors in server output

## 9. Test with Real Audio (Future)

Once STT/AI is added, you can test with real audio files:

```python
# Future: Test with real audio
import wave
import websockets

async def send_real_audio():
    with wave.open("audio.wav", "rb") as wav:
        # Read and send frames
        pass
```

## Summary

The easiest way to check:
1. Start server: `uvicorn app.main:app --reload`
2. Run test: `python test_streaming.py`
3. Check logs for queue/dispatcher activity

If server starts and test script runs without errors, everything is working! ✅
