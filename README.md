# AI-Based Illegal Waste Dump Detection

Phase 1 provides a local foundation for tracking suspected illegal-waste locations. It includes a React/Vite dashboard, a FastAPI API, and PostgreSQL/PostGIS persistence.

## Phase 1 scope

Implemented: health reporting, cookie-based Argon2 authentication, protected case APIs, uploader-owned report dashboard, 3–5 photo report intake with GPS checks, private image metadata/evidence links, coordinate validation, detected-case creation, readable case codes such as `DMP-000001`, PostGIS point storage, and a live dashboard connected to the API.

Not implemented yet: AI inference, satellite imagery ingestion, Google Maps or Street View preview, S3 image uploads (local private storage is used until S3 is configured), password reset, municipal inspection APIs, notifications, and cleanup workflow APIs.

## Prerequisites

- PostgreSQL with the PostGIS extension
- Git
- Node.js 20+ and npm (for running the frontend outside Docker)
- Python 3.12+ (for running the backend outside Docker)

## Windows PowerShell setup

Run the native PostgreSQL, backend, and frontend setup below from this project root. The services use ports 5173 (frontend), 8000 (backend), and 5432 (PostgreSQL). Open:

- Dashboard: http://localhost:5173
- Swagger API docs: http://localhost:8000/docs
- Health: http://localhost:8000/api/v1/health
- Cases: http://localhost:8000/api/v1/cases

Authentication routes: `POST /api/v1/auth/signup`, `POST /api/v1/auth/login`, `POST /api/v1/auth/logout`, and `GET /api/v1/auth/me`. Uploader routes include `GET /api/v1/my/dashboard`, `POST /api/v1/my/reports`, and `GET /api/v1/my/reports/{case_id}`. Sessions use an HttpOnly, SameSite cookie containing a random token whose SHA-256 hash is stored in `auth_sessions`; passwords use Argon2id hashes and are never returned.

## API smoke tests

```powershell
Invoke-RestMethod http://localhost:8000/api/v1/health
Invoke-RestMethod http://localhost:8000/api/v1/cases

$body = @{ latitude = 12.9716; longitude = 77.5946; waste_category = "unknown" } | ConvertTo-Json
Invoke-RestMethod -Uri http://localhost:8000/api/v1/cases -Method Post -ContentType "application/json" -Body $body
```

Latitude must be between -90 and 90. Longitude must be between -180 and 180. Cases are saved in the database and return with status `suspected`.

## Local development

Install PostgreSQL with the PostGIS extension first. Create the application user and database from a PostgreSQL administrator prompt:

```powershell
psql -U postgres
```

Run these SQL statements in the `psql` prompt:

```sql
CREATE USER app_user WITH PASSWORD 'change_me_locally';
CREATE DATABASE illegal_dump_detection OWNER app_user;
\q
```

Initialize PostGIS and the Phase 1 schema:

```powershell
$env:PGPASSWORD = "change_me_locally"
psql -h localhost -U app_user -d illegal_dump_detection -f database\init.sql
```

If the local PostgreSQL installation does not allow `app_user` to create the PostGIS extension, run the schema command once with the PostgreSQL administrator instead, then grant the application user access to the created tables and sequences.

Backend:

```powershell
Set-Location "D:\Illegal Waste Dump Detection"
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r backend\requirements.txt
$env:DATABASE_URL = "postgresql+psycopg://app_user:change_me_locally@localhost:5432/illegal_dump_detection"
$env:CORS_ORIGINS = "http://localhost:5173"
$env:SESSION_COOKIE_SECURE = "false"
uvicorn app.main:app --app-dir backend --reload
```

Frontend:

```powershell
Set-Location "D:\Illegal Waste Dump Detection\frontend"
$env:VITE_API_BASE_URL = "http://localhost:8000"
npm install
npm run dev
npm run build
```

Keep the backend and frontend running in separate PowerShell windows. Do not run `python main.py`: the application entry point is `backend\app\main.py` and it is served by Uvicorn.

## Managed PostgreSQL

For a managed PostgreSQL service such as Aiven, copy its connection URL into the local `.env` as `DATABASE_URL`. Never commit the real URL or paste it into chat.

```dotenv
DATABASE_URL=postgresql://<user>:<password>@<host>:<port>/<database>?sslmode=require
VITE_API_BASE_URL=http://127.0.0.1:8000
```

The backend automatically converts `postgresql://` or `postgres://` schemes to the installed `psycopg` SQLAlchemy driver. Initialize the remote schema once from PowerShell using the provider URL:

```powershell
$env:DATABASE_URL = "postgresql://<user>:<password>@<host>:<port>/<database>?sslmode=require"
psql $env:DATABASE_URL -f database\init.sql
```

The managed PostgreSQL instance must support the PostGIS extension because `dump_cases.location` is a PostGIS geography. If `database\init.sql` reports that `postgis` is unavailable, enable the extension in the provider or use a PostgreSQL provider that supports it before starting the backend.

For an existing database, apply the auth migration without dropping data:

```powershell
python -c "from pathlib import Path; import psycopg; from dotenv import dotenv_values; c=psycopg.connect(dotenv_values('.env')['DATABASE_URL']); c.execute(Path('database/migrations/002_auth_sessions.sql').read_text()); c.commit(); c.close()"
```

The migration creates only `auth_sessions`; it does not delete or recreate existing tables.

Apply the uploader ownership migration to an existing database without resetting data:

```powershell
psql $env:DATABASE_URL -f database\migrations\003_uploader_reports.sql
```

The uploader flow stores uploaded files under the private `private_uploads` directory until an S3 provider is configured. The directory is ignored by Git and is not served publicly.

## Database lifecycle

Run `database/init.sql` once against the local database. It creates PostGIS and all eight foundation tables. The script is safe to rerun for its schema objects, but it does not migrate existing data. To reset local data, drop and recreate only the development database with PostgreSQL tools.

Keep the backend and frontend running in separate PowerShell windows. If a port is occupied, stop the conflicting process or change the development server port and use the matching URL. If the backend reports an unavailable database, verify that the PostgreSQL service is running and that `DATABASE_URL` uses `localhost`, not the old Compose hostname `db`.

## Project layout

- `frontend/` React + Vite dashboard
- `backend/` FastAPI application with organized settings, database, schemas, and routes
- `database/init.sql` PostGIS schema
- `docs/PHASE_1_REPORT.md` implementation and validation report
