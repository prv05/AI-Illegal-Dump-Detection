from io import BytesIO
from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from fastapi.responses import FileResponse
from PIL import Image, UnidentifiedImageError
from sqlalchemy import text
from sqlalchemy.engine import Connection

from .auth import get_current_user
from .db import get_connection
from .schemas import DashboardReport, EvidenceItem, ReportCreated, UploaderDashboard, UserResponse

router = APIRouter(prefix="/api/v1/my")
PROJECT_ROOT = Path(__file__).resolve().parents[2]
UPLOAD_ROOT = PROJECT_ROOT / "private_uploads"
ALLOWED_TYPES = {"image/jpeg", "image/png", "image/webp"}
ALLOWED_CATEGORIES = {
    "mixed_household",
    "construction_demolition",
    "plastic",
    "electronic",
    "green_garden",
    "industrial_chemical",
    "other",
}
MAX_FILE_SIZE = 10 * 1024 * 1024


def require_uploader(user: UserResponse) -> UserResponse:
    if user.role != "uploader":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Uploader access required")
    return user


def gps_from_image(data: bytes) -> tuple[float, float] | None:
    try:
        with Image.open(BytesIO(data)) as image:
            exif = image.getexif()
            gps = exif.get(34853)
            if not gps:
                return None
            latitude = gps.get(2)
            longitude = gps.get(4)
            if not latitude or not longitude:
                return None
            lat = float(latitude[0]) + float(latitude[1]) / 60 + float(latitude[2]) / 3600
            lon = float(longitude[0]) + float(longitude[1]) / 60 + float(longitude[2]) / 3600
            if gps.get(1) == "S":
                lat = -lat
            if gps.get(3) == "W":
                lon = -lon
            if not -90 <= lat <= 90 or not -180 <= lon <= 180:
                return None
            return lat, lon
    except (UnidentifiedImageError, KeyError, TypeError, ValueError, ZeroDivisionError):
        return None


def report_row(connection: Connection, user_id: int, case_id: int):
    return connection.execute(
        text(
            """
            SELECT c.id, c.case_code,
                   ST_Y(c.location::geometry) AS latitude,
                   ST_X(c.location::geometry) AS longitude,
                   c.status, COALESCE(c.category, 'other') AS waste_category,
                   c.source, c.created_at,
                   COUNT(ce.id)::int AS evidence_count
            FROM dump_cases c
            LEFT JOIN case_evidence ce ON ce.dump_case_id = c.id
            WHERE c.id = :case_id AND c.submitted_by = :user_id
            GROUP BY c.id
            """
        ),
        {"case_id": case_id, "user_id": user_id},
    ).mappings().first()


def evidence_rows(connection: Connection, user_id: int, case_id: int) -> list[EvidenceItem]:
    rows = connection.execute(
        text(
            """
            SELECT ia.id, ia.original_filename, ia.mime_type
            FROM case_evidence ce
            JOIN image_assets ia ON ia.id = ce.image_asset_id
            JOIN dump_cases c ON c.id = ce.dump_case_id
            WHERE ce.dump_case_id = :case_id AND c.submitted_by = :user_id
            ORDER BY ce.created_at
            """
        ),
        {"case_id": case_id, "user_id": user_id},
    ).mappings()
    return [EvidenceItem(id=row["id"], original_filename=row["original_filename"] or "Submitted photo", mime_type=row["mime_type"] or "image/jpeg", url=f"/api/v1/my/reports/{case_id}/evidence/{row['id']}") for row in rows]


@router.get("/dashboard", response_model=UploaderDashboard)
def dashboard(
    current_user: UserResponse = Depends(get_current_user),
    connection: Connection = Depends(get_connection),
) -> UploaderDashboard:
    require_uploader(current_user)
    counts = connection.execute(
        text(
            """
            SELECT COUNT(*)::int AS total,
                   COUNT(*) FILTER (WHERE status = 'pending_verification')::int AS awaiting_review,
                   COUNT(*) FILTER (WHERE status = 'needs_more_evidence')::int AS needs_more_evidence,
                   COUNT(*) FILTER (WHERE status IN ('verified', 'cleanup_assigned'))::int AS confirmed,
                   COUNT(*) FILTER (WHERE status = 'rejected')::int AS rejected,
                   COUNT(*) FILTER (WHERE status IN ('cleaned', 'closed'))::int AS resolved
            FROM dump_cases
            WHERE submitted_by = :user_id
            """
        ),
        {"user_id": current_user.id},
    ).mappings().one()
    rows = connection.execute(
        text(
            """
            SELECT c.id, c.case_code,
                   ST_Y(c.location::geometry) AS latitude,
                   ST_X(c.location::geometry) AS longitude,
                   c.status, COALESCE(c.category, 'other') AS waste_category,
                   c.source, c.created_at,
                   COUNT(ce.id)::int AS evidence_count
            FROM dump_cases c
            LEFT JOIN case_evidence ce ON ce.dump_case_id = c.id
            WHERE c.submitted_by = :user_id
            GROUP BY c.id
            ORDER BY c.created_at DESC
            LIMIT 12
            """
        ),
        {"user_id": current_user.id},
    ).mappings()
    return UploaderDashboard(counts=dict(counts), recent_reports=[DashboardReport(**row) for row in rows])


@router.get("/reports/{case_id}", response_model=DashboardReport)
def report_details(
    case_id: int,
    current_user: UserResponse = Depends(get_current_user),
    connection: Connection = Depends(get_connection),
) -> DashboardReport:
    require_uploader(current_user)
    row = report_row(connection, current_user.id, case_id)
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Report not found")
    return DashboardReport(**row, evidence=evidence_rows(connection, current_user.id, case_id))


@router.get("/reports/{case_id}/evidence/{asset_id}")
def evidence_image(
    case_id: int,
    asset_id: int,
    current_user: UserResponse = Depends(get_current_user),
    connection: Connection = Depends(get_connection),
):
    require_uploader(current_user)
    asset = connection.execute(
        text(
            """
            SELECT ia.storage_key, ia.mime_type, ia.original_filename
            FROM image_assets ia
            JOIN case_evidence ce ON ce.image_asset_id = ia.id
            JOIN dump_cases c ON c.id = ce.dump_case_id
            WHERE ia.id = :asset_id AND ce.dump_case_id = :case_id AND c.submitted_by = :user_id
            """
        ),
        {"asset_id": asset_id, "case_id": case_id, "user_id": current_user.id},
    ).mappings().first()
    if not asset:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Evidence not found")
    path = UPLOAD_ROOT / asset["storage_key"]
    if not path.is_file():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Evidence file is unavailable")
    return FileResponse(path, media_type=asset["mime_type"], filename=asset["original_filename"] or "evidence")


@router.post("/reports/{case_id}/evidence", response_model=DashboardReport)
async def add_evidence(
    case_id: int,
    files: list[UploadFile] = File(...),
    current_user: UserResponse = Depends(get_current_user),
    connection: Connection = Depends(get_connection),
) -> DashboardReport:
    require_uploader(current_user)
    row = report_row(connection, current_user.id, case_id)
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Report not found")
    if row["status"] != "needs_more_evidence":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Additional evidence is not requested for this report")
    if not 1 <= len(files) <= 5:
        raise HTTPException(status_code=422, detail="Select between 1 and 5 photos")

    saved_paths: list[Path] = []
    try:
        UPLOAD_ROOT.mkdir(parents=True, exist_ok=True)
        for file in files:
            if file.content_type not in ALLOWED_TYPES:
                raise HTTPException(status_code=422, detail="Only JPEG, PNG, and WebP photos are accepted")
            data = await file.read()
            if len(data) > MAX_FILE_SIZE:
                raise HTTPException(status_code=413, detail="Each photo must be 10 MB or smaller")
            object_name = f"{current_user.id}/{uuid4().hex}{Path(file.filename or '').suffix.lower()}"
            path = UPLOAD_ROOT / object_name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(data)
            saved_paths.append(path)
            asset = connection.execute(
                text(
                    """
                    INSERT INTO image_assets (source_type, storage_provider, storage_key, uploaded_by,
                                              mime_type, file_size_bytes, original_filename, metadata)
                    VALUES ('field_photo', 'local', :storage_key, :user_id, :mime_type, :file_size, :filename, CAST(:metadata AS jsonb))
                    RETURNING id
                    """
                ),
                {"storage_key": object_name, "user_id": current_user.id, "mime_type": file.content_type, "file_size": len(data), "filename": file.filename, "metadata": "{}"},
            ).mappings().one()
            connection.execute(
                text("INSERT INTO case_evidence (dump_case_id, image_asset_id, evidence_type, added_by) VALUES (:case_id, :asset_id, 'field_photo', :user_id)"),
                {"case_id": case_id, "asset_id": asset["id"], "user_id": current_user.id},
            )
        connection.commit()
        updated = report_row(connection, current_user.id, case_id)
        return DashboardReport(**updated, evidence=evidence_rows(connection, current_user.id, case_id))
    except HTTPException:
        connection.rollback()
        for path in saved_paths:
            path.unlink(missing_ok=True)
        raise
    except Exception as exc:
        connection.rollback()
        for path in saved_paths:
            path.unlink(missing_ok=True)
        raise HTTPException(status_code=503, detail="Could not save additional evidence") from exc


@router.post("/reports", response_model=ReportCreated, status_code=status.HTTP_201_CREATED)
async def create_report(
    files: list[UploadFile] = File(...),
    waste_category: str = Form(...),
    latitude: float | None = Form(default=None, ge=-90, le=90),
    longitude: float | None = Form(default=None, ge=-180, le=180),
    description: str = Form(default=""),
    current_user: UserResponse = Depends(get_current_user),
    connection: Connection = Depends(get_connection),
) -> ReportCreated:
    require_uploader(current_user)
    if not 3 <= len(files) <= 5:
        raise HTTPException(status_code=422, detail="Select between 3 and 5 photos")
    if waste_category not in ALLOWED_CATEGORIES:
        raise HTTPException(status_code=422, detail="Choose a valid waste category")

    prepared: list[tuple[UploadFile, bytes, tuple[float, float] | None]] = []
    for file in files:
        if file.content_type not in ALLOWED_TYPES:
            raise HTTPException(status_code=422, detail="Only JPEG, PNG, and WebP photos are accepted")
        data = await file.read()
        if len(data) > MAX_FILE_SIZE:
            raise HTTPException(status_code=413, detail="Each photo must be 10 MB or smaller")
        prepared.append((file, data, gps_from_image(data)))

    gps_points = [point for _, _, point in prepared if point]
    if latitude is None or longitude is None:
        if not gps_points:
            raise HTTPException(status_code=422, detail="Confirm a map location or provide photos with GPS metadata")
        latitude, longitude = gps_points[0]
    if any(abs(point[0] - latitude) > 0.01 or abs(point[1] - longitude) > 0.01 for point in gps_points):
        raise HTTPException(status_code=422, detail="Photo GPS locations differ; confirm one location manually")

    saved_paths: list[Path] = []
    try:
        UPLOAD_ROOT.mkdir(parents=True, exist_ok=True)
        created = connection.execute(
            text(
                """
                INSERT INTO dump_cases (location, category, status, source, submitted_by, reported_at, description)
                VALUES (ST_SetSRID(ST_MakePoint(:longitude, :latitude), 4326)::geography,
                        :category, 'pending_verification', 'uploader', :user_id, now(), :description)
                RETURNING id, case_code, status, created_at
                """
            ),
            {"longitude": longitude, "latitude": latitude, "category": waste_category, "user_id": current_user.id, "description": description.strip() or None},
        )
        created = created.mappings().one()
        connection.execute(
            text(
                """
                INSERT INTO notifications (user_id, title, message, notification_type, related_case_id)
                VALUES (:user_id, 'Report submitted', 'Your report has been received and is awaiting review.', 'case_update', :case_id)
                """
            ),
            {"user_id": current_user.id, "case_id": created["id"]},
        )
        case_id = created["id"]
        for file, data, point in prepared:
            object_name = f"{current_user.id}/{uuid4().hex}{Path(file.filename or '').suffix.lower()}"
            path = UPLOAD_ROOT / object_name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(data)
            saved_paths.append(path)
            asset = connection.execute(
                text(
                    """
                    INSERT INTO image_assets (source_type, storage_provider, storage_key, uploaded_by,
                                              latitude, longitude, mime_type, file_size_bytes, original_filename, metadata)
                    VALUES ('field_photo', 'local', :storage_key, :user_id, :latitude, :longitude,
                            :mime_type, :file_size, :filename, CAST(:metadata AS jsonb))
                    RETURNING id
                    """
                ),
                {"storage_key": object_name, "user_id": current_user.id, "latitude": point[0] if point else latitude, "longitude": point[1] if point else longitude, "mime_type": file.content_type, "file_size": len(data), "filename": file.filename, "metadata": "{}"},
            )
            asset_id = asset.mappings().one()["id"]
            connection.execute(
                text("INSERT INTO case_evidence (dump_case_id, image_asset_id, evidence_type, added_by) VALUES (:case_id, :asset_id, 'field_photo', :user_id)"),
                {"case_id": case_id, "asset_id": asset_id, "user_id": current_user.id},
            )
        connection.commit()
        return ReportCreated(id=case_id, case_code=created["case_code"], status=created["status"], photo_count=len(prepared), created_at=created["created_at"])
    except Exception as exc:
        connection.rollback()
        for path in saved_paths:
            path.unlink(missing_ok=True)
        raise HTTPException(status_code=503, detail="Could not save the report") from exc
