"""Knowledge retrieval service interface."""

from abc import ABC, abstractmethod

from app.knowledge.schemas.retrieval import RetrievalQuery, RetrievalResult


class RetrievalService(ABC):
    @abstractmethod
    async def retrieve(self, query: RetrievalQuery) -> RetrievalResult:
        raise NotImplementedError
