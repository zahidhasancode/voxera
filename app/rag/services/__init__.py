"""Enterprise RAG service port."""

from abc import ABC, abstractmethod

from app.rag.interfaces.models import EnterpriseRAGResult, RetrievalRequest


class EnterpriseRAGServicePort(ABC):
    @abstractmethod
    async def execute(self, request: RetrievalRequest) -> EnterpriseRAGResult:
        raise NotImplementedError
