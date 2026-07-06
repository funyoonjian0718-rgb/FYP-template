from datetime import datetime

from pydantic import BaseModel, EmailStr, Field

#account creation and login 
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

#Waht the APi sends back to the user
class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"

class UserProfileUpdateRequest(BaseModel):
    type2_diabetes: bool | None = None
    age: int | None = Field(default=None, ge=1, le=120)
    weight_kg: float | None = Field(default=None, ge=1, le=500)
    activity_level: str | None = None

#password recovery 
class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str = Field(min_length=8)

#what the user will see if they check the user profile
class UserProfileResponse(BaseModel):
    id: int
    email: EmailStr
    type2_diabetes: bool
    age: int | None
    weight_kg: int | None
    activity_level: str | None
    created_at: datetime

