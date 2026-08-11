from uuid import UUID

from pydantic import BaseModel, EmailStr, Field

from app.schemas.common import SuccessResponse


class RegisterRequest(BaseModel):
    name: str = Field(..., min_length=2)
    email: EmailStr
    password: str = Field(..., min_length=6)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=6)


class UserResponse(BaseModel):
    id: UUID
    name: str
    email: str
    role: str


class AuthData(BaseModel):
    token: str
    user: UserResponse


class AuthResponse(SuccessResponse[AuthData]):
    pass


class CurrentUserResponse(SuccessResponse[UserResponse]):
    pass
