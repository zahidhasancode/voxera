"""Prometheus metrics exposition (operational observability)."""

from __future__ import annotations

from fastapi import APIRouter, Response

from app.core.observability import platform_metrics
from app.streaming.metrics import streaming_metrics
from app.voice.turn_metrics import voice_latency_stats

router = APIRouter()


def _render_prometheus() -> str:
    snap = platform_metrics.snapshot()
    voice = voice_latency_stats.snapshot()
    lines = [
        "# HELP voxera_http_requests_total Total HTTP requests processed",
        "# TYPE voxera_http_requests_total counter",
        f"voxera_http_requests_total {snap['request_count']}",
        "# HELP voxera_http_errors_total Total HTTP error responses",
        "# TYPE voxera_http_errors_total counter",
        f"voxera_http_errors_total {snap['error_count']}",
        "# HELP voxera_http_timeouts_total Total request timeouts",
        "# TYPE voxera_http_timeouts_total counter",
        f"voxera_http_timeouts_total {snap['timeout_count']}",
        "# HELP voxera_rate_limits_total Total rate-limited requests",
        "# TYPE voxera_rate_limits_total counter",
        f"voxera_rate_limits_total {snap['rate_limit_count']}",
        "# HELP voxera_http_latency_avg_ms Average request latency",
        "# TYPE voxera_http_latency_avg_ms gauge",
        f"voxera_http_latency_avg_ms {snap['latency_avg_ms']}",
        "# HELP voxera_http_latency_p95_ms P95 request latency",
        "# TYPE voxera_http_latency_p95_ms gauge",
        f"voxera_http_latency_p95_ms {snap['latency_p95_ms']}",
        "# HELP voxera_http_latency_p99_ms P99 request latency",
        "# TYPE voxera_http_latency_p99_ms gauge",
        f"voxera_http_latency_p99_ms {snap['latency_p99_ms']}",
        "# HELP voxera_audio_queue_wait_ms Time the latest audio frame waited in the inbound queue (not voice latency)",
        "# TYPE voxera_audio_queue_wait_ms gauge",
        f"voxera_audio_queue_wait_ms {round(streaming_metrics.current_latency_ms, 2)}",
        "# HELP voxera_voice_turns_total User turns answered",
        "# TYPE voxera_voice_turns_total counter",
        f"voxera_voice_turns_total {voice['turns']}",
        "# HELP voxera_voice_interruptions_total Replies stopped by barge-in",
        "# TYPE voxera_voice_interruptions_total counter",
        f"voxera_voice_interruptions_total {voice['interruptions']}",
        "# HELP voxera_voice_first_audio_ms Final transcript to first audio frame sent, rolling window",
        "# TYPE voxera_voice_first_audio_ms summary",
        f'voxera_voice_first_audio_ms{{quantile="0.5"}} {voice["first_audio_p50_ms"]}',
        f'voxera_voice_first_audio_ms{{quantile="0.95"}} {voice["first_audio_p95_ms"]}',
        "# HELP voxera_voice_llm_first_token_ms Final transcript to first LLM token, rolling window",
        "# TYPE voxera_voice_llm_first_token_ms summary",
        f'voxera_voice_llm_first_token_ms{{quantile="0.5"}} {voice["llm_first_token_p50_ms"]}',
        f'voxera_voice_llm_first_token_ms{{quantile="0.95"}} {voice["llm_first_token_p95_ms"]}',
        "# HELP voxera_voice_dropped_frames_total Dropped audio frames",
        "# TYPE voxera_voice_dropped_frames_total counter",
        f"voxera_voice_dropped_frames_total {streaming_metrics.dropped_frames}",
        "# HELP voxera_voice_queue_depth Current voice queue depth",
        "# TYPE voxera_voice_queue_depth gauge",
        f"voxera_voice_queue_depth {streaming_metrics.queue_depth}",
    ]
    for name, count in snap.get("exception_counts", {}).items():
        safe = name.replace('"', "").replace("\n", "")
        lines.extend([
            '# TYPE voxera_exceptions_total counter',
            f'voxera_exceptions_total{{type="{safe}"}} {count}',
        ])
    for name, count in snap.get("dependency_failures", {}).items():
        safe = name.replace('"', "").replace("\n", "")
        lines.extend([
            '# TYPE voxera_dependency_failures_total counter',
            f'voxera_dependency_failures_total{{dependency="{safe}"}} {count}',
        ])
    return "\n".join(lines) + "\n"


@router.get("")
async def prometheus_metrics() -> Response:
    """Prometheus text exposition format."""
    return Response(content=_render_prometheus(), media_type="text/plain; version=0.0.4; charset=utf-8")
