from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import text
from sqlalchemy.engine import Connection

from .db import check_database, get_connection
from .schemas import CaseCreate, CaseResponse, HealthResponse

router = APIRouter(prefix="/api/v1")


@router.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    database_status = "available" if check_database() else "unavailable"
    return HealthResponse(api="available", database=database_status)


@router.get("/cases", response_model=list[CaseResponse])
def list_cases(
    status_filter: Literal[
        "detected", "pending_verification", "verified", "rejected",
        "needs_more_evidence", "cleanup_assigned", "cleaned", "closed", "duplicate",
    ] | None = Query(default=None, alias="status"),
    limit: int = Query(default=100, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    connection: Connection = Depends(get_connection),
) -> list[CaseResponse]:
    query = """
        SELECT id, case_code, ST_Y(location::geometry) AS latitude,
               ST_X(location::geometry) AS longitude, status, category AS waste_category,
               source, created_at
        FROM dump_cases
    """
    parameters: dict[str, object] = {"limit": limit, "offset": offset}
    if status_filter:
        query += " WHERE status = :status"
        parameters["status"] = status_filter
    query += " ORDER BY created_at DESC LIMIT :limit OFFSET :offset"
    rows = connection.execute(text(query), parameters).mappings()
    return [CaseResponse(**row) for row in rows]


@router.post("/cases", response_model=CaseResponse, status_code=status.HTTP_201_CREATED)
def create_case(payload: CaseCreate, connection: Connection = Depends(get_connection)) -> CaseResponse:
    try:
        row = connection.execute(
            text(
                """
                INSERT INTO dump_cases (location, status, category, source)
                VALUES (ST_SetSRID(ST_MakePoint(:longitude, :latitude), 4326)::geography, 'detected', :waste_category, 'manual')
                RETURNING id, case_code, ST_Y(location::geometry) AS latitude,
                          ST_X(location::geometry) AS longitude, status, category AS waste_category,
                          source, created_at
                """
            ),
            payload.model_dump(),
        ).mappings().one()
        connection.commit()
        return CaseResponse(**row)
    except Exception as exc:
        connection.rollback()
        raise HTTPException(status_code=503, detail="Database operation failed") from exc
