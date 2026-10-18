from datetime import datetime, timedelta, timezone
import hashlib
import secrets

from fastapi import Cookie, Depends, HTTPException, Response, status
from pwdlib import PasswordHash
from sqlalchemy import text
from sqlalchemy.engine import Connection

from .config import get_settings
from .db import get_connection
from .schemas import UserResponse

password_hash = PasswordHash.recommended()


def hash_session_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def issue_session(connection: Connection, user_id: int, response: Response) -> None:
    settings = get_settings()
    raw_token = secrets.token_urlsafe(32)
    expires_at = datetime.now(timezone.utc) + timedelta(days=settings.session_days)
    connection.execute(
        text("INSERT INTO auth_sessions (user_id, token_hash, expires_at) VALUES (:user_id, :token_hash, :expires_at)"),
        {"user_id": user_id, "token_hash": hash_session_token(raw_token), "expires_at": expires_at},
    )
    connection.commit()
    response.set_cookie(
        settings.session_cookie_name,
        raw_token,
        max_age=settings.session_days * 24 * 60 * 60,
        httponly=True,
        secure=settings.session_cookie_secure,
        samesite="lax",
        path="/",
    )


def user_from_session(session_token: str | None, connection: Connection) -> UserResponse:
    if not session_token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required")
    row = connection.execute(
        text(
            """
            SELECT u.id, u.name, u.email, u.role, u.is_active, u.created_at
            FROM auth_sessions s
            JOIN users u ON u.id = s.user_id
            WHERE s.token_hash = :token_hash
              AND s.expires_at > now()
              AND u.is_active = true
            """
        ),
        {"token_hash": hash_session_token(session_token)},
    ).mappings().first()
    if not row:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required")
    connection.execute(
        text("UPDATE auth_sessions SET last_seen_at = now() WHERE token_hash = :token_hash"),
        {"token_hash": hash_session_token(session_token)},
    )
    connection.commit()
    return UserResponse(**row)


def get_current_user(
    session_token: str | None = Cookie(default=None, alias="wastewatch_session"),
    connection: Connection = Depends(get_connection),
) -> UserResponse:
    return user_from_session(session_token, connection)
