# AI-Based Illegal Waste Dump Detection

Phase 1 provides a local foundation for tracking suspected illegal-waste locations. It includes a React/Vite dashboard, a FastAPI API, and PostgreSQL/PostGIS persistence.

## Phase 1 scope

Implemented: health reporting, recent case listing, coordinate validation, suspected-case creation, readable case codes such as `DMP-000001`, PostGIS point storage, and a live dashboard connected to the API.

Not implemented yet: AI inference, satellite imagery ingestion, Google Maps or Street View, image uploads, authentication, municipal inspection, notifications, and cleanup workflows.

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

## Database lifecycle

Run `database/init.sql` once against the local database. It creates PostGIS and all eight foundation tables. The script is safe to rerun for its schema objects, but it does not migrate existing data. To reset local data, drop and recreate only the development database with PostgreSQL tools.

Keep the backend and frontend running in separate PowerShell windows. If a port is occupied, stop the conflicting process or change the development server port and use the matching URL. If the backend reports an unavailable database, verify that the PostgreSQL service is running and that `DATABASE_URL` uses `localhost`, not the old Compose hostname `db`.

## Project layout

- `frontend/` React + Vite dashboard
- `backend/` FastAPI application with organized settings, database, schemas, and routes
- `database/init.sql` PostGIS schema
- `docs/PHASE_1_REPORT.md` implementation and validation report
