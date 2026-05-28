from __future__ import annotations

from app.rag.constraints import validate_answer
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
        food_metadata: list[dict] | None = None,
    ) -> tuple[str, list[RetrievedSnippet]]:
        retrieved = self.retrieve(question)
        prompt = build_prompt(
            user_context=user_context,
            question=question,
            selected_food=selected_food,
            portion=portion,
            retrieved=retrieved,
            food_metadata=food_metadata,
        )
        output = generation_service.generate(prompt)

        violations = validate_answer(output, question)
        if violations:
            warning_block = "\n\nValidation Notes:\n" + "\n".join(f"- {v}" for v in violations)
            output = f"{output.rstrip()}\n{warning_block}"

        return output, retrieved


rag_service = RAGService()

