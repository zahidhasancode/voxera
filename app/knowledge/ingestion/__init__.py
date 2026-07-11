"""Knowledge ingestion package."""

from app.knowledge.ingestion.background import BackgroundIngestionProcessor
from app.knowledge.ingestion.metrics import ProcessingMetricsCollector
from app.knowledge.ingestion.pipeline import IngestionPipeline
from app.knowledge.ingestion.stages import STAGE_PROGRESS, clean_text, progress_for_stage

__all__ = [
    "BackgroundIngestionProcessor",
    "IngestionPipeline",
    "ProcessingMetricsCollector",
    "STAGE_PROGRESS",
    "clean_text",
    "progress_for_stage",
]
