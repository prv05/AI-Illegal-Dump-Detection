from collections.abc import Generator

from fastapi import HTTPException, status
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Connection, Engine
from sqlalchemy.exc import SQLAlchemyError

from .config import get_settings

engine: Engine = create_engine(get_settings().sqlalchemy_database_url, pool_pre_ping=True)


def get_connection() -> Generator[Connection, None, None]:
    try:
        with engine.connect() as connection:
            yield connection
    except SQLAlchemyError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database is temporarily unavailable",
        ) from exc


def check_database() -> bool:
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        return True
    except Exception:
        return False
