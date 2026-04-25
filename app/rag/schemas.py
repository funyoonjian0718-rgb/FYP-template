from pydantic import BaseModel, Field


class DietaryQueryRequest(BaseModel):
    query_text: str = Field(min_length=1, max_length=2000)
    selected_food: str | None = Field(default=None, max_length=128)
    portion: str | None = Field(default=None, pattern="^(small|medium|large)$")
    free_text_food: str | None = Field(default=None, max_length=256)


class ReferenceSnippet(BaseModel):
    source: str
    snippet: str


class DietaryQueryResponse(BaseModel):
    formatted_answer: str
    references: list[ReferenceSnippet]

