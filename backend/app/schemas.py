from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, field_validator, model_validator


class UserCreate(BaseModel):
    full_name: str = Field(min_length=2, max_length=120)
    email: str = Field(min_length=5, max_length=320)
    password: str = Field(min_length=8, max_length=128)
    password_confirmation: str = Field(min_length=8, max_length=128)

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value: str) -> str:
        normalized = value.strip().lower()
        if "@" not in normalized or normalized.startswith("@") or normalized.endswith("@"):
            raise ValueError("Enter a valid email address")
        return normalized

    @model_validator(mode="after")
    def passwords_match(self):
        if self.password != self.password_confirmation:
            raise ValueError("Passwords do not match")
        if not any(character.isupper() for character in self.password) or not any(character.isdigit() for character in self.password):
            raise ValueError("Password must include an uppercase letter and a number")
        return self


class LoginRequest(BaseModel):
    email: str = Field(min_length=5, max_length=320)
    password: str = Field(min_length=1, max_length=128)

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value: str) -> str:
        return value.strip().lower()


class UserResponse(BaseModel):
    id: int
    name: str
    email: str
    role: Literal["admin", "inspector", "uploader"]
    is_active: bool
    created_at: datetime


class CaseCreate(BaseModel):
    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)
    waste_category: str = Field(default="unknown", min_length=1, max_length=80)


class CaseResponse(BaseModel):
    id: int
    case_code: str
    latitude: float
    longitude: float
    status: Literal[
        "detected",
        "pending_verification",
        "verified",
        "rejected",
        "needs_more_evidence",
        "cleanup_assigned",
        "cleaned",
        "closed",
        "duplicate",
    ]
    waste_category: str
    source: str
    created_at: datetime


class HealthResponse(BaseModel):
    api: str
    database: str
