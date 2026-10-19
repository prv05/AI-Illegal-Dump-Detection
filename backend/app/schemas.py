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


class PasswordChange(BaseModel):
    current_password: str = Field(min_length=1, max_length=128)
    new_password: str = Field(min_length=8, max_length=128)
    new_password_confirmation: str = Field(min_length=8, max_length=128)

    @model_validator(mode="after")
    def validate_password(self):
        if self.new_password != self.new_password_confirmation:
            raise ValueError("Passwords do not match")
        if not any(character.isupper() for character in self.new_password) or not any(character.isdigit() for character in self.new_password):
            raise ValueError("Password must include an uppercase letter and a number")
        return self


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


class DashboardReport(BaseModel):
    id: int
    case_code: str
    latitude: float
    longitude: float
    status: str
    waste_category: str
    source: str
    created_at: datetime
    evidence_count: int
    evidence: list["EvidenceItem"] = Field(default_factory=list)


class EvidenceItem(BaseModel):
    id: int
    original_filename: str
    mime_type: str
    url: str


class UploaderDashboard(BaseModel):
    counts: dict[str, int]
    recent_reports: list[DashboardReport]


class ReportCreated(BaseModel):
    id: int
    case_code: str
    status: str
    photo_count: int
    created_at: datetime


class NotificationResponse(BaseModel):
    id: int
    title: str
    message: str
    notification_type: str
    related_case_id: int | None
    is_read: bool
    created_at: datetime
    read_at: datetime | None


class HealthResponse(BaseModel):
    api: str
    database: str
