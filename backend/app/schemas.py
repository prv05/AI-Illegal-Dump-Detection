from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class CaseCreate(BaseModel):
    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)
    waste_category: str = Field(default="unknown", min_length=1, max_length=80)


class CaseResponse(BaseModel):
    id: int
    case_code: str
    latitude: float
    longitude: float
    status: Literal["suspected", "confirmed", "rejected", "resolved"]
    waste_category: str
    source: str
    created_at: datetime


class HealthResponse(BaseModel):
    api: str
    database: str
