from collections.abc import Generator

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Connection, Engine

from .config import get_settings

engine: Engine = create_engine(get_settings().sqlalchemy_database_url, pool_pre_ping=True)


def get_connection() -> Generator[Connection, None, None]:
    with engine.connect() as connection:
        yield connection


def check_database() -> bool:
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        return True
    except Exception:
        return False
