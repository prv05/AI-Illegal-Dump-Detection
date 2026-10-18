from fastapi import APIRouter, Depends, HTTPException, status
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
def list_cases(connection: Connection = Depends(get_connection)) -> list[CaseResponse]:
    rows = connection.execute(
        text(
            """
            SELECT id, case_code, ST_Y(location) AS latitude,
                   ST_X(location) AS longitude, status, waste_category,
                   source, created_at
            FROM dump_cases
            ORDER BY created_at DESC
            LIMIT 100
            """
        )
    ).mappings()
    return [CaseResponse(**row) for row in rows]


@router.post("/cases", response_model=CaseResponse, status_code=status.HTTP_201_CREATED)
def create_case(payload: CaseCreate, connection: Connection = Depends(get_connection)) -> CaseResponse:
    try:
        row = connection.execute(
            text(
                """
                INSERT INTO dump_cases (location, status, waste_category, source)
                VALUES (ST_SetSRID(ST_MakePoint(:longitude, :latitude), 4326), 'suspected', :waste_category, 'manual')
                RETURNING id, case_code, ST_Y(location) AS latitude,
                          ST_X(location) AS longitude, status, waste_category,
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
