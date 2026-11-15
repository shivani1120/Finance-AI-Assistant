from enum import StrEnum

from pydantic import BaseModel, Field, field_validator


class UserRole(StrEnum):
    USER = "user"
    ADMIN = "admin"


class UserCreate(BaseModel):
    email: str = Field(min_length=3, max_length=320)
    password: str = Field(min_length=12, max_length=128)

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value: str) -> str:
        email = value.strip().lower()
        if email.count("@") != 1 or "." not in email.rsplit("@", 1)[-1]:
            raise ValueError("Enter a valid email address")
        return email


class UserRead(BaseModel):
    id: int
    email: str
    role: UserRole

    model_config = {"from_attributes": True}


class RoleUpdate(BaseModel):
    role: UserRole


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
