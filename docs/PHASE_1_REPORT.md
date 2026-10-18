# Phase 1 Report

Date: 2026-10-18

## Completed

- Created the repository scaffold in the existing project root.
- Added React/Vite/TypeScript dashboard with live case loading, connection status, loading, empty, and error states.
- Added suspected-case form with latitude and longitude constraints and waste category selection.
- Added FastAPI `/docs`, `/api/v1/health`, `/api/v1/cases` GET, and `/api/v1/cases` POST endpoints.
- Added parameterized SQLAlchemy queries and PostGIS point creation using longitude as X and latitude as Y.
- Added all eight required database tables, constraints, timestamps, spatial indexes, workflow indexes, PostGIS extension, and readable case-code sequence.
- Expanded the schema to cover users, private image/S3 metadata, detection runs, model detections, case evidence, inspection history, and cleanup attempts with audit-preserving foreign keys.
- Added geography(Point, 4326) case locations, risk/severity/status constraints, JSONB metadata, update timestamp triggers, pagination/status filtering, and the complete workflow status model.
- Updated the API to read and create cases against the expanded `category` and `detected` schema while preserving the frontend's `waste_category` field.
- Added Argon2id signup/login/logout/current-user endpoints with HttpOnly cookie sessions and a non-destructive `auth_sessions` migration applied to Aiven.
- Added React Router public auth pages, protected application routes, role-aware navigation, and honest placeholder pages for workflows without real backend endpoints.
- Removed container-specific files so the project currently runs through native Windows services.
- Added `.env.example`, `.gitignore`, Windows PowerShell setup instructions, and reset/volume guidance.

## Validation run

- `python -m compileall -q backend/app`: passed.
- `python -c "from app.main import app ..."` from `backend`: passed; valid coordinates accepted and invalid latitude rejected.
- `npm install` from `frontend`: passed; npm reported 0 vulnerabilities.
- `npm run build` from `frontend`: passed; Vite generated the production bundle.
- Previous managed-database connection check: passed.
- Previous provider `CREATE EXTENSION IF NOT EXISTS postgis`: failed because that provider reported `extension "postgis" is not available`.
- `database/migrations/002_auth_sessions.sql` against Aiven: passed.
- Auth smoke test against Aiven: signup, `/me`, logout, and login passed; new signup role was `uploader`.
- Unauthenticated case request returned `401`.
- Frontend build after auth routing: passed; Vite emitted a chunk-size warning due to Three.js.

## Runtime status

The expanded schema, Aiven migration, authentication API, and frontend build are working. The auth smoke test created a disposable `example.test` uploader account in Aiven. npm reported three high-severity advisories after adding React Router; no force-upgrade was applied. The initial baseline did not contain a Git checkout, and the linked GitHub repository was confirmed empty, so no existing application code was overwritten.

## Known issues and deferred work

- The map is an explicitly labelled placeholder.
- AI inference, satellite imagery, Street View, S3 uploads, password reset, inspection APIs, notifications, and cleanup APIs remain deferred.
- `database/init.sql` is a clean bootstrap; `database/migrations/002_auth_sessions.sql` is the first non-destructive migration.

## Highest-priority Phase 2 task

Add the real detection-run and inspection APIs behind the protected page shells, beginning with durable image ingestion and a background job boundary before introducing a model.
