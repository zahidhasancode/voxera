"""Structured verifier model — fast validation without LLM."""

from app.verifier.interfaces.verifier_model import VerifierModel
from app.verifier.schemas import VerifierInput, VerifierResult
from app.verifier.validators.pipeline import ValidationPipeline


class StructuredVerifierModel(VerifierModel):
    def __init__(self, pipeline: ValidationPipeline | None = None) -> None:
        self._pipeline = pipeline or ValidationPipeline()

    @property
    def provider_name(self) -> str:
        return "structured"

    async def health(self) -> dict:
        return {"status": "healthy", "provider": self.provider_name}

    def estimate_tokens(self, verifier_input: VerifierInput) -> int:
        parts = [
            str(verifier_input.planner_output.model_dump()),
            str(verifier_input.working_memory),
            " ".join(verifier_input.retrieved_knowledge),
        ]
        return sum(max(1, len(p) // 4) for p in parts)

    async def verify(self, verifier_input: VerifierInput) -> VerifierResult:
        _, result = self._pipeline.run(verifier_input)
        return result
