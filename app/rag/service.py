from __future__ import annotations

from app.rag.generation import generation_service
from app.rag.prompting import build_prompt
from app.rag.retrieval import retrieval_service
from app.rag.types import RetrievedSnippet


class RAGService:
    def retrieve(self, question: str, k: int | None = None) -> list[RetrievedSnippet]:
        return retrieval_service.retrieve(question, k=k)

    def answer(
        self,
        *,
        user_context: dict,
        question: str,
        selected_food: str | None,
        portion: str | None,
    ) -> tuple[str, list[RetrievedSnippet]]:
        retrieved = self.retrieve(question)
        prompt = build_prompt(
            user_context=user_context,
            question=question,
            selected_food=selected_food,
            portion=portion,
            retrieved=retrieved,
        )
        output = generation_service.generate(prompt)
        return output, retrieved


rag_service = RAGService()

