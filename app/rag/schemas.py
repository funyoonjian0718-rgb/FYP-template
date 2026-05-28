from pydantic import BaseModel, Field


class DietaryQueryRequest(BaseModel):
    query_text: str = Field(min_length=1, max_length=2000)
    selected_food: str | None = Field(default=None, max_length=128)
    portion: str | None = Field(default=None, pattern="^(small|medium|large)$")
    free_text_food: str | None = Field(default=None, max_length=256)


class ReferenceSnippet(BaseModel):
    source: str
    snippet: str


class FoodNutritionResponse(BaseModel):
    name: str
    category: str | None = None
    serving_size: str | None = None
    calories: int | None = None
    carbohydrates_g: float | None = None
    protein_g: float | None = None
    fat_g: float | None = None
    fibre_g: float | None = None
    sugar_g: float | None = None
    sodium_mg: int | None = None
    glycemic_index: str | None = None
    health_advice: str | None = None
    diabetes_suitable: bool | str | None = None
    alternatives: str | None = None
    price_myr: float | None = None


class DietaryQueryResponse(BaseModel):
    formatted_answer: str
    references: list[ReferenceSnippet]

