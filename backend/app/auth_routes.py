from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from sqlalchemy import text
from sqlalchemy.engine import Connection

from .auth import get_current_user, hash_session_token, issue_session, password_hash
from .db import get_connection
from .schemas import LoginRequest, UserCreate, UserResponse

router = APIRouter(prefix="/api/v1/auth")


@router.post("/signup", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def signup(payload: UserCreate, response: Response, connection: Connection = Depends(get_connection)) -> UserResponse:
    try:
        row = connection.execute(
            text(
                """
                INSERT INTO users (name, email, password_hash, role)
                VALUES (:name, :email, :password_hash, 'uploader')
                RETURNING id, name, email, role, is_active, created_at
                """
            ),
            {"name": payload.full_name.strip(), "email": payload.email, "password_hash": password_hash.hash(payload.password)},
        ).mappings().one()
        connection.commit()
        issue_session(connection, row["id"], response)
        return UserResponse(**row)
    except Exception as exc:
        connection.rollback()
        if "duplicate key" in str(exc).lower() or "unique" in str(exc).lower():
            raise HTTPException(status_code=400, detail="Unable to create account with those details") from exc
        raise HTTPException(status_code=503, detail="Unable to create account") from exc


@router.post("/login", response_model=UserResponse)
def login(payload: LoginRequest, response: Response, connection: Connection = Depends(get_connection)) -> UserResponse:
    row = connection.execute(
        text("SELECT id, name, email, password_hash, role, is_active, created_at FROM users WHERE lower(email) = :email"),
        {"email": payload.email},
    ).mappings().first()
    if not row or not row["is_active"] or not row["password_hash"] or not password_hash.verify(payload.password, row["password_hash"]):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")
    issue_session(connection, row["id"], response)
    return UserResponse(**{key: row[key] for key in ("id", "name", "email", "role", "is_active", "created_at")})


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(response: Response, request: Request, connection: Connection = Depends(get_connection)) -> None:
    from .config import get_settings

    token = request.cookies.get(get_settings().session_cookie_name)
    if token:
        connection.execute(text("DELETE FROM auth_sessions WHERE token_hash = :token_hash"), {"token_hash": hash_session_token(token)})
        connection.commit()
    response.delete_cookie(get_settings().session_cookie_name, path="/")


@router.get("/me", response_model=UserResponse)
def me(current_user: UserResponse = Depends(get_current_user)) -> UserResponse:
    return current_user
