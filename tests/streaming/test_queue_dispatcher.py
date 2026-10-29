"""Audio frame queue and dispatcher: drop-oldest backpressure, event wake-up, order, clean stop."""

import asyncio
import time

from app.streaming.audio_queue import AudioFrameQueue
from app.streaming.dispatcher import StreamingDispatcher


async def test_full_queue_drops_the_oldest_frame() -> None:
    q = AudioFrameQueue(max_size=3)
    for i in range(5):
        await q.enqueue(bytes([i]))
    assert q.frames_dropped == 2
    got = [(await q.dequeue()).frame for _ in range(3)]
    assert got == [b"\x02", b"\x03", b"\x04"]
    assert await q.dequeue() is None


async def test_wait_for_frame_times_out_when_empty() -> None:
    q = AudioFrameQueue()
    assert await q.wait_for_frame(timeout=0.01) is False


async def test_wait_for_frame_wakes_as_soon_as_a_frame_arrives() -> None:
    q = AudioFrameQueue()
    waiter = asyncio.create_task(q.wait_for_frame(timeout=1.0))
    await asyncio.sleep(0.01)
    started = time.perf_counter()
    await q.enqueue(b"x")
    assert await waiter is True
    assert time.perf_counter() - started < 0.05


async def test_dispatcher_forwards_frames_in_order_and_promptly() -> None:
    q = AudioFrameQueue()
    seen: list[tuple[bytes, float]] = []

    async def on_frame(frame: bytes) -> None:
        seen.append((frame, time.perf_counter()))

    d = StreamingDispatcher(q, on_frame)
    await d.start()
    await asyncio.sleep(0.05)  # dispatcher is now idle, waiting on the queue's event
    sent_at = time.perf_counter()
    for i in range(5):
        await q.enqueue(bytes([i]))
    for _ in range(100):
        if len(seen) == 5:
            break
        await asyncio.sleep(0.005)
    await d.stop()

    assert [f for f, _ in seen] == [bytes([i]) for i in range(5)]
    # An idle dispatcher picks up a new frame immediately, not after a polling tick.
    assert seen[0][1] - sent_at < 0.02


async def test_idle_dispatcher_stops_quickly() -> None:
    d = StreamingDispatcher(AudioFrameQueue(), lambda frame: asyncio.sleep(0))
    await d.start()
    await asyncio.sleep(0.02)
    started = time.perf_counter()
    await d.stop()
    assert time.perf_counter() - started < 0.5
    assert not d.is_running()
