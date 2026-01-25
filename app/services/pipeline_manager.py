"""Manager for audio pipelines."""

from typing import Dict, Optional

from app.core.logger import get_logger
from app.services.audio_pipeline import AudioPipeline

logger = get_logger(__name__)


class PipelineManager:
    """Manages audio pipelines for multiple call sessions."""

    def __init__(self):
        """Initialize pipeline manager."""
        self._pipelines: Dict[str, AudioPipeline] = {}

    def create_pipeline(self, call_id: str) -> AudioPipeline:
        """Create a new audio pipeline for a call.

        Args:
            call_id: Call session ID

        Returns:
            AudioPipeline instance
        """
        if call_id in self._pipelines:
            return self._pipelines[call_id]

        pipeline = AudioPipeline(call_id)
        self._pipelines[call_id] = pipeline
        logger.debug(f"Created audio pipeline for call {call_id}")
        return pipeline

    def get_pipeline(self, call_id: str) -> Optional[AudioPipeline]:
        """Get pipeline by call_id.

        Args:
            call_id: Call session ID

        Returns:
            AudioPipeline if found, None otherwise
        """
        return self._pipelines.get(call_id)

    async def remove_pipeline(self, call_id: str) -> None:
        """Remove and stop pipeline.

        Args:
            call_id: Call session ID
        """
        pipeline = self._pipelines.pop(call_id, None)
        if pipeline:
            await pipeline.stop()
            logger.debug(f"Removed audio pipeline for call {call_id}")

    def list_pipelines(self) -> list[str]:
        """List all active pipeline call IDs.

        Returns:
            List of call IDs
        """
        return list(self._pipelines.keys())

    def get_pipeline_count(self) -> int:
        """Get total number of active pipelines.

        Returns:
            Number of pipelines
        """
        return len(self._pipelines)


# Global pipeline manager
pipeline_manager = PipelineManager()
