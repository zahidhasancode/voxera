"""Pipeline stage helpers and progress mapping."""

from app.core.enums import KnowledgeProcessingStage

STAGE_PROGRESS: dict[KnowledgeProcessingStage, int] = {
    KnowledgeProcessingStage.UPLOAD: 5,
    KnowledgeProcessingStage.PARSE: 20,
    KnowledgeProcessingStage.CLEAN: 30,
    KnowledgeProcessingStage.CHUNK: 45,
    KnowledgeProcessingStage.METADATA: 50,
    KnowledgeProcessingStage.EMBED: 75,
    KnowledgeProcessingStage.VECTOR_STORE: 90,
    KnowledgeProcessingStage.COMPLETE: 100,
    KnowledgeProcessingStage.FAILED: 0,
}


def progress_for_stage(stage: KnowledgeProcessingStage) -> int:
    return STAGE_PROGRESS.get(stage, 0)


def clean_text(text: str) -> str:
    """Normalize whitespace and strip control characters."""
    lines = [line.strip() for line in text.splitlines()]
    cleaned = "\n".join(line for line in lines if line)
    return cleaned.strip()
