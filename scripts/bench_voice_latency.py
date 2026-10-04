#!/usr/bin/env python3
"""Measure voice latency the way a caller experiences it.

Plays recorded speech into the voice WebSocket at the real 20 ms cadence (like a
microphone), keeps sending silence afterwards, and times what comes back:

  end of speech -> final transcript      (speech recognition + end-of-turn detection)
  end of speech -> first LLM token
  end of speech -> first audio frame     (the number a caller feels)

"End of speech" is the moment the last frame containing speech was sent, with
trailing silence in the file trimmed. With --barge-in it also measures how long
the reply keeps coming after the caller starts talking over it.

Usage:
  python scripts/bench_voice_latency.py --url ws://localhost:8000/api/v1/ --turns 20
  python scripts/bench_voice_latency.py --wav my_speech/*.wav --barge-in --json out.json

Audio files must be WAV, mono, 16-bit, 16 kHz. Samples are in scripts/bench_audio/.
The server must be running; the provider names it reports are printed with the result.
"""

from __future__ import annotations

import argparse
import asyncio
import glob
import json
import math
import os
import statistics
import struct
import sys
import time
import wave

import websockets

FRAME_BYTES = 640  # 20 ms, PCM16 mono, 16 kHz
FRAME_SECONDS = 0.02
SILENCE = b"\x00" * FRAME_BYTES


def frame_energy(frame: bytes) -> float:
    n = len(frame) // 2
    if not n:
        return 0.0
    return sum(abs(s) for s in struct.unpack(f"<{n}h", frame[: n * 2])) / n


def load_wav(path: str) -> list[bytes]:
    with wave.open(path, "rb") as w:
        if (w.getnchannels(), w.getsampwidth(), w.getframerate()) != (1, 2, 16000):
            raise SystemExit(f"{path}: need mono 16-bit 16 kHz WAV")
        data = w.readframes(w.getnframes())
    frames = [data[i : i + FRAME_BYTES].ljust(FRAME_BYTES, b"\x00") for i in range(0, len(data), FRAME_BYTES)]
    while frames and frame_energy(frames[-1]) < 200:  # trim trailing silence: speech ends at the last loud frame
        frames.pop()
    while frames and frame_energy(frames[0]) < 200:
        frames.pop(0)
    return frames


def tone(seconds: float = 1.0) -> list[bytes]:
    n = int(16000 * seconds)
    data = struct.pack(f"<{n}h", *(int(5000 * math.sin(2 * math.pi * 300 * i / 16000)) for i in range(n)))
    return [data[i : i + FRAME_BYTES].ljust(FRAME_BYTES, b"\x00") for i in range(0, len(data), FRAME_BYTES)]


class Mic:
    """Sends one frame every 20 ms forever: queued speech if there is any, silence otherwise."""

    def __init__(self, ws) -> None:
        self.ws = ws
        self.pending: list[bytes] = []
        self.speech_started_at: float | None = None
        self.speech_ended_at: float | None = None
        self._task = asyncio.create_task(self._run())

    def say(self, frames: list[bytes]) -> None:
        self.speech_started_at = None
        self.speech_ended_at = None
        self.pending = list(frames)

    async def _run(self) -> None:
        next_at = time.monotonic()
        while True:
            if self.pending:
                frame = self.pending.pop(0)
                await self.ws.send(frame)
                now = time.monotonic()
                if self.speech_started_at is None:
                    self.speech_started_at = now
                if not self.pending:
                    self.speech_ended_at = now
            else:
                await self.ws.send(SILENCE)
            next_at += FRAME_SECONDS
            await asyncio.sleep(max(0.0, next_at - time.monotonic()))

    async def close(self) -> None:
        self._task.cancel()
        await asyncio.gather(self._task, return_exceptions=True)


def pct(values: list[float], q: float) -> float:
    if not values:
        return float("nan")
    s = sorted(values)
    return s[min(len(s) - 1, max(0, round(q * (len(s) - 1))))]


def summarise(name: str, values: list[float]) -> str:
    if not values:
        return f"  {name:<46} no samples"
    return (
        f"  {name:<46} median {statistics.median(values):7.0f} ms   p95 {pct(values, 0.95):7.0f} ms"
        f"   min {min(values):6.0f}   max {max(values):6.0f}   n={len(values)}"
    )


async def run(args: argparse.Namespace) -> dict:
    paths = sorted(p for pattern in args.wav for p in glob.glob(pattern))
    utterances = [load_wav(p) for p in paths] if paths else [tone()]
    results: list[dict] = []
    barge: list[dict] = []

    async with websockets.connect(args.url, max_size=None) as ws:
        hello = json.loads(await ws.recv())
        providers = hello.get("providers", {})
        print(f"connected: providers={providers} audio={hello.get('audio')}")
        mic = Mic(ws)
        try:
            for turn in range(args.turns):
                frames = utterances[turn % len(utterances)]
                rec: dict = {"turn": turn + 1}
                mic.say(frames)
                state = {"final": None, "token": None, "audio": None, "clear": None, "barge_at": None, "after_clear": 0}
                barge_pending = args.barge_in
                deadline = time.monotonic() + args.timeout
                done = False
                while not done and time.monotonic() < deadline:
                    try:
                        msg = await asyncio.wait_for(ws.recv(), timeout=0.05)
                    except asyncio.TimeoutError:
                        msg = None
                    now = time.monotonic()
                    eos = mic.speech_ended_at
                    if isinstance(msg, (bytes, bytearray)):
                        if state["clear"] is not None:
                            if not state.get("next_reply"):
                                state["after_clear"] += 1  # audio of the stopped reply arriving after the stop
                        elif state["audio"] is None and eos is not None and state["barge_at"] is None:
                            state["audio"] = now
                    elif msg is not None:
                        ev = json.loads(msg)
                        kind = ev.get("type")
                        if kind == "final" and eos is not None and state["final"] is None:
                            state["final"] = now
                        elif kind == "llm_partial" and state["token"] is None and state["final"] is not None:
                            state["token"] = now
                        elif kind == "turn_metrics" and state["barge_at"] is None and state["final"] is not None:
                            # Only the reply to the whole utterance counts. A pause inside the
                            # recording can end a turn early; that reply is interrupted by the
                            # rest of the speech and is not what we are timing.
                            rec["server"] = ev
                            done = not barge_pending
                        elif kind == "tts_clear" and state["barge_at"] is not None and state["clear"] is None:
                            state["clear"] = now
                        elif kind == "tts_start" and state["clear"] is not None:
                            state["next_reply"] = True  # a new reply has begun; its audio is not a leak
                        elif kind == "error":
                            rec["error"] = ev
                            done = True
                    # barge-in: talk over the reply 400 ms after it starts
                    if barge_pending and state["audio"] is not None and now - state["audio"] > 0.4:
                        barge_pending = False
                        eos_first = mic.speech_ended_at
                        mic.say(utterances[(turn + 1) % len(utterances)])
                        state["barge_at"] = now
                        rec.update(_measure(eos_first, state))
                    if state["clear"] is not None and now - state["clear"] > 1.5:
                        barge.append({
                            "speech_start_to_reply_stopped_ms": (state["clear"] - state["barge_at"]) * 1000.0,
                            "audio_frames_after_stop": state["after_clear"],
                        })
                        mic.pending = []  # stop the interrupting speech; let the pipeline settle
                        await asyncio.sleep(args.pause + 2.0)
                        done = True
                if "end_of_speech_to_first_audio_ms" not in rec:
                    rec.update(_measure(mic.speech_ended_at, state))
                results.append(rec)
                print(
                    f"turn {turn + 1:>3}: final {fmt(rec.get('end_of_speech_to_final_transcript_ms'))}  "
                    f"first token {fmt(rec.get('end_of_speech_to_first_llm_token_ms'))}  "
                    f"first audio {fmt(rec.get('end_of_speech_to_first_audio_ms'))}"
                    + (f"  ERROR {rec['error'].get('code')}" if "error" in rec else "")
                )
                await asyncio.sleep(args.pause)
        finally:
            await mic.close()

    def col(key: str) -> list[float]:
        return [r[key] for r in results if r.get(key) is not None]

    def server(key: str) -> list[float]:
        return [r["server"][key] for r in results if r.get("server") and r["server"].get(key) is not None]

    print(f"\nproviders: {providers}   turns: {len(results)}   audio files: {len(paths) or 'generated tone'}")
    print("measured by this client (includes network to the server):")
    print(summarise("end of speech -> final transcript", col("end_of_speech_to_final_transcript_ms")))
    print(summarise("end of speech -> first LLM token", col("end_of_speech_to_first_llm_token_ms")))
    print(summarise("end of speech -> first audio", col("end_of_speech_to_first_audio_ms")))
    print("reported by the server (starts at the final transcript):")
    print(summarise("final transcript -> first LLM token", server("transcript_final_to_llm_first_token_ms")))
    print(summarise("final transcript -> first audio", server("transcript_final_to_first_audio_ms")))
    if barge:
        print("barge-in:")
        print(summarise("caller starts talking -> reply stopped", [b["speech_start_to_reply_stopped_ms"] for b in barge]))
        print(f"  audio frames received after the stop signal: max {max(b['audio_frames_after_stop'] for b in barge)}")
    if any(v == "mock" for v in providers.values()):
        print("\nNOTE: at least one provider is the built-in mock. These numbers show pipeline overhead,")
        print("      not real speech recognition, language model or speech synthesis latency.")
    return {"providers": providers, "turns": results, "barge_in": barge}


def _measure(eos: float | None, state: dict) -> dict:
    def ms(t: float | None) -> float | None:
        return None if (t is None or eos is None) else round((t - eos) * 1000.0, 1)

    return {
        "end_of_speech_to_final_transcript_ms": ms(state["final"]),
        "end_of_speech_to_first_llm_token_ms": ms(state["token"]),
        "end_of_speech_to_first_audio_ms": ms(state["audio"]),
    }


def fmt(v: float | None) -> str:
    return "   —   " if v is None else f"{v:6.0f} ms"


def main() -> None:
    here = os.path.dirname(os.path.abspath(__file__))
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--url", default="ws://localhost:8000/api/v1/")
    ap.add_argument("--wav", nargs="*", default=[os.path.join(here, "bench_audio", "*.wav")])
    ap.add_argument("--turns", type=int, default=10)
    ap.add_argument("--pause", type=float, default=1.0, help="seconds of silence between turns")
    ap.add_argument("--timeout", type=float, default=30.0, help="give up on a turn after this many seconds")
    ap.add_argument("--barge-in", action="store_true", help="talk over each reply and time how fast it stops")
    ap.add_argument("--json", help="write raw results to this file")
    args = ap.parse_args()
    try:
        out = asyncio.run(run(args))
    except (OSError, websockets.exceptions.WebSocketException) as exc:
        sys.exit(f"could not run the benchmark against {args.url}: {exc}")
    if args.json:
        with open(args.json, "w") as f:
            json.dump(out, f, indent=2)
        print(f"raw results written to {args.json}")


if __name__ == "__main__":
    main()
