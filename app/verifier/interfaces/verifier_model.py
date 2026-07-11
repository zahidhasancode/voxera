"""Verifier model provider interface."""

from abc import ABC, abstractmethod

from app.verifier.schemas import VerifierInput, VerifierResult


class VerifierModel(ABC):
    @abstractmethod
    async def verify(self, verifier_input: VerifierInput) -> VerifierResult:
        ...

    @abstractmethod
    async def health(self) -> dict:
        ...

    @abstractmethod
    def estimate_tokens(self, verifier_input: VerifierInput) -> int:
        ...

    @property
    @abstractmethod
    def provider_name(self) -> str:
        ...
