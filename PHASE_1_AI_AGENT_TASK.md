# Phase 1 --- Foundation Setup

## AI Agent Execution Task \| AI-Based Illegal Waste Dump Detection

**Target date:** 18 October 2026\
**Project:** AI-Based Illegal Waste Dump Detection\
**Phase:** 1 --- Repository, frontend, backend, database, and Docker
foundation\
**Priority:** Critical\
**Execution mode:** Work autonomously in the existing project
repository. Do not stop after writing a plan; implement, run, test, and
document the result.

------------------------------------------------------------------------

## 1. Mission

Prepare a working local development foundation for the AI-Based Illegal
Waste Dump Detection application.

The system will eventually support: 1. Satellite-area selection and
satellite-image uploads. 2. AI screening of satellite imagery for
suspected illegal dumping. 3. Street-level review using Google Street
View where available and uploaded field photographs. 4. Municipal
inspection and confirmation. 5. A map of suspected, confirmed, rejected,
and resolved cases.

**Today's scope is only Phase 1.** Do not attempt to build the AI
models, Google Maps integration, image-upload pipeline, or full
inspection workflow today. Make the foundation reliable so these can be
added in later phases.

## 2. Starting point

Use the existing project scaffold if available:

``` text
ai-illegal-dump-detection/
├── frontend/        # React + Vite
├── backend/         # FastAPI
├── database/
│   └── init.sql     # PostgreSQL/PostGIS schema
├── docker-compose.yml
├── .env.example
├── .gitignore
└── README.md
```

If the repository is missing or the scaffold differs, inspect the actual
files first. Preserve working code and adapt it instead of blindly
overwriting it. Do not create a second nested project directory.

## 3. Required technology

-   Frontend: React, Vite, TypeScript
-   Backend: Python, FastAPI, Uvicorn
-   Database: PostgreSQL with PostGIS
-   Database access: SQLAlchemy and psycopg
-   Local services: Docker Compose
-   Version control: Git

Use compatible stable package versions. Avoid adding unnecessary
frameworks or services.

## 4. Work items

### A. Inspect the project and establish a baseline

-   [ ] Inspect all existing project files and Git status.
-   [ ] Identify missing files, broken imports, inconsistent
    environment-variable names, and incorrect paths.
-   [ ] Check whether Docker Desktop, Docker Compose, Git, Node.js, and
    Python are available.
-   [ ] Do not overwrite user changes or delete data without explicit
    authorization.
-   [ ] Record any environment limitation that prevents a test from
    running.

### B. Repository hygiene

-   [ ] Ensure the project has a clear root `README.md`.
-   [ ] Ensure `.gitignore` excludes `.env`, local credentials,
    `node_modules`, Python caches, virtual environments, uploaded data,
    datasets, and model weights.
-   [ ] Keep `.env.example` committed with safe placeholder values only.
-   [ ] Ensure frontend and backend remain separate folders.
-   [ ] Add clear setup and troubleshooting instructions for Windows
    PowerShell.
-   [ ] Do not commit API keys, passwords, private datasets, or trained
    weights.

### C. Frontend foundation

-   [ ] Ensure the React/Vite application starts successfully.
-   [ ] Provide a clean dashboard for the waste-detection project.
-   [ ] Include a backend/database connection indicator.
-   [ ] Include a basic case summary and recent-cases table.
-   [ ] Include a temporary map placeholder clearly labelled as not yet
    integrated.
-   [ ] Include a small form to create a **suspected** test case with
    latitude and longitude.
-   [ ] Load cases from the backend instead of using hard-coded case
    rows.
-   [ ] Show useful loading, empty, and error states.
-   [ ] Confirm the production build command succeeds.
-   [ ] Do not imply that AI inference or Google Maps already works.

### D. FastAPI backend

-   [ ] Ensure the FastAPI application starts and exposes Swagger docs
    at `/docs`.
-   [ ] Add `GET /api/v1/health` with API and database health
    information.
-   [ ] Add `GET /api/v1/cases` to list recent cases.
-   [ ] Add `POST /api/v1/cases` to create a suspected case.
-   [ ] Validate latitude in `[-90, 90]` and longitude in `[-180, 180]`.
-   [ ] Use parameterized SQL or safe ORM operations; do not concatenate
    user input into SQL.
-   [ ] Return consistent JSON and useful HTTP status codes.
-   [ ] Configure CORS for the local frontend only during development.
-   [ ] Keep routes, configuration, and database access organized rather
    than placing all application logic in one oversized file.
-   [ ] Do not add a fake AI endpoint that returns invented predictions.

### E. PostgreSQL/PostGIS database

-   [ ] Configure a PostgreSQL image with PostGIS support in Docker
    Compose.
-   [ ] Initialize the schema from `database/init.sql` on first database
    creation.
-   [ ] Create and verify these tables:
    -   `users`
    -   `image_assets`
    -   `detection_runs`
    -   `dump_cases`
    -   `detections`
    -   `case_evidence`
    -   `inspections`
    -   `cleanup_records`
-   [ ] Ensure `dump_cases.location` uses a PostGIS point with SRID
    4326.
-   [ ] Ensure coordinates are stored in the correct order: longitude as
    X, latitude as Y.
-   [ ] Add useful spatial and workflow-status indexes.
-   [ ] Check primary keys, foreign keys, check constraints, and
    timestamp defaults.
-   [ ] Ensure case creation generates a unique readable code such as
    `DMP-000001`.
-   [ ] Ensure database initialization is repeatable on a fresh
    database.
-   [ ] Document that initialization scripts do not rerun automatically
    on an already initialized Docker volume.
-   [ ] Do not run `docker compose down -v` unless the user explicitly
    approves deleting local database data.

### F. Docker Compose

-   [ ] Configure separate services for frontend, backend, and database.
-   [ ] Add a database health check.
-   [ ] Ensure the backend waits for the database to become healthy.
-   [ ] Ensure frontend and backend environment variables use consistent
    names.
-   [ ] Keep source-code mounts usable for local development.
-   [ ] Verify expected ports:
    -   Frontend: `5173`
    -   Backend: `8000`
    -   PostgreSQL: `5432`
-   [ ] Ensure the containers can communicate using the Compose service
    name `db`.
-   [ ] Make startup and shutdown instructions explicit.

### G. Documentation

Update `README.md` with: - \[ \] Project purpose and Phase 1 scope. - \[
\] Prerequisites. - \[ \] Windows PowerShell setup commands. - \[ \]
Environment configuration. - \[ \] Docker start/stop commands. - \[ \]
Frontend, API docs, and health URLs. - \[ \] Database
initialization/reset explanation. - \[ \] Common startup and
port-conflict troubleshooting. - \[ \] Clear list of features not yet
implemented.

Add a short `docs/PHASE_1_REPORT.md` documenting files changed, tests
run, test outcomes, and known issues.

## 5. Required local commands

Use the project root as the working directory.

### Start the stack

``` powershell
Copy-Item .env.example .env
docker compose config
docker compose up --build -d
docker compose ps
```

If `.env` already exists, preserve it; do not overwrite user settings.

### Check service logs

``` powershell
docker compose logs --tail=100 db
docker compose logs --tail=100 backend
docker compose logs --tail=100 frontend
```

### Verify endpoints

``` powershell
Invoke-RestMethod http://localhost:8000/api/v1/health
Invoke-RestMethod http://localhost:8000/api/v1/cases
```

### Test creating a case

``` powershell
$body = @{
  latitude = 12.9716
  longitude = 77.5946
  waste_category = "unknown"
} | ConvertTo-Json

Invoke-RestMethod `
  -Uri http://localhost:8000/api/v1/cases `
  -Method Post `
  -ContentType "application/json" `
  -Body $body
```

Then call the list endpoint and verify the new case is returned with a
unique case code and the correct coordinates.

**Do not claim a command passed unless it was actually run and its
output checked.** If Docker or internet access is unavailable, perform
static checks and state clearly which runtime checks remain blocked.

## 6. Acceptance criteria

Phase 1 is complete only when all applicable criteria below pass:

1.  [ ] `docker compose config` validates the Compose configuration.
2.  [ ] Frontend, backend, and PostGIS database start successfully, or
    any environmental blocker is documented with evidence.
3.  [ ] `GET /api/v1/health` reports the database as available.
4.  [ ] `GET /api/v1/cases` returns valid JSON.
5.  [ ] `POST /api/v1/cases` creates a suspected case with valid
    coordinates.
6.  [ ] The created case appears in the next list request and survives a
    backend/container restart.
7.  [ ] Invalid coordinates are rejected with a client error.
8.  [ ] The frontend can load cases from the API and create a test case.
9.  [ ] `npm run build` succeeds.
10. [ ] The database contains all eight required tables and the PostGIS
    extension.
11. [ ] No credentials or private keys are committed.
12. [ ] `README.md` and `docs/PHASE_1_REPORT.md` accurately describe the
    final state.
13. [ ] All known failures and unfinished items are listed honestly.

## 7. Guardrails

-   Do not deploy to AWS or another public host today.
-   Do not create or push to a remote GitHub repository unless valid
    access is available and the user has authorized the action.
-   Do not delete databases, volumes, files, or existing user work to
    make tests pass.
-   Do not expose database credentials or API keys in logs, screenshots,
    or documentation.
-   Do not claim model predictions, satellite map integration, Street
    View, image uploads, authentication, or municipal verification are
    implemented unless they are genuinely implemented and tested.
-   Keep this phase focused on a dependable local foundation.

## 8. Final report format

At the end of the task, provide a concise report containing:

1.  **Completed:** concrete changes made.
2.  **Validation:** commands run and actual results.
3.  **How to run:** exact commands and URLs.
4.  **Blockers:** anything not working and the evidence.
5.  **Not in Phase 1:** features intentionally deferred.
6.  **Next task:** the single highest-priority step for Phase 2.

Do not stop at generating this checklist. Execute the work against the
existing repository, make the required changes, run the tests that the
environment allows, and report the actual outcome.
