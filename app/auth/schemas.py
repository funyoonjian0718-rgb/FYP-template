from pydantic import BaseModel, EmailStr, Field


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)

    type2_diabetes: bool
    age: int | None = Field(default=None, ge=1, le=120)
    weight_kg: int | None = Field(default=None, ge=1, le=500)
    activity_level: str | None = Field(default=None)  # Removed pattern to allow empty/null


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str = Field(min_length=8)


class UserProfileResponse(BaseModel):
    id: int
    email: EmailStr
    type2_diabetes: bool
    age: int | None
    weight_kg: int | None
    activity_level: str | None

