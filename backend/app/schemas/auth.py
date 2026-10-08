"""Registration request and safe public-user response schemas."""

from datetime import datetime

from pydantic import BaseModel, EmailStr, Field, SecretStr, field_validator


class RegisterRequest(BaseModel):
    email: EmailStr
    username: str = Field(min_length=3, max_length=30, pattern=r"^[A-Za-z0-9_]+$")
    password: SecretStr = Field(min_length=8, max_length=128)

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value: EmailStr) -> str:
        return str(value).strip().lower()

    @field_validator("username")
    @classmethod
    def normalize_username(cls, value: str) -> str:
        return value.strip().lower()

    @field_validator("password")
    @classmethod
    def require_letters_and_numbers(cls, value: SecretStr) -> SecretStr:
        password = value.get_secret_value()
        if not any(char.isalpha() for char in password) or not any(
            char.isdigit() for char in password
        ):
            raise ValueError("Password must contain at least one letter and one number.")
        return value


class UserResponse(BaseModel):
    id: str
    email: EmailStr
    username: str
    created_at: datetime
    updated_at: datetime


class LoginRequest(BaseModel):
    username_or_email: str = Field(min_length=1, max_length=254)
    password: SecretStr = Field(min_length=1, max_length=128)


class AccessTokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
