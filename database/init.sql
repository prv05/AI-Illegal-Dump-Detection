CREATE EXTENSION IF NOT EXISTS postgis;
CREATE SEQUENCE IF NOT EXISTS dump_case_code_seq;

CREATE TABLE IF NOT EXISTS users (
    id BIGSERIAL PRIMARY KEY,
    email TEXT NOT NULL UNIQUE,
    full_name TEXT NOT NULL,
    role TEXT NOT NULL DEFAULT 'reviewer' CHECK (role IN ('admin', 'reviewer', 'inspector')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE TABLE IF NOT EXISTS image_assets (
    id BIGSERIAL PRIMARY KEY,
    uploaded_by BIGINT REFERENCES users(id),
    storage_key TEXT NOT NULL UNIQUE,
    source_type TEXT NOT NULL CHECK (source_type IN ('satellite', 'field_photo', 'other')),
    captured_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE TABLE IF NOT EXISTS detection_runs (
    id BIGSERIAL PRIMARY KEY,
    image_asset_id BIGINT NOT NULL REFERENCES image_assets(id) ON DELETE CASCADE,
    model_name TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'queued' CHECK (status IN ('queued', 'running', 'completed', 'failed')),
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE TABLE IF NOT EXISTS dump_cases (
    id BIGSERIAL PRIMARY KEY,
    case_code TEXT NOT NULL UNIQUE DEFAULT ('DMP-' || lpad(nextval('dump_case_code_seq')::text, 6, '0')),
    location GEOMETRY(Point, 4326) NOT NULL,
    status TEXT NOT NULL DEFAULT 'suspected' CHECK (status IN ('suspected', 'confirmed', 'rejected', 'resolved')),
    waste_category TEXT NOT NULL DEFAULT 'unknown',
    source TEXT NOT NULL DEFAULT 'manual',
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE TABLE IF NOT EXISTS detections (
    id BIGSERIAL PRIMARY KEY,
    detection_run_id BIGINT NOT NULL REFERENCES detection_runs(id) ON DELETE CASCADE,
    dump_case_id BIGINT REFERENCES dump_cases(id) ON DELETE SET NULL,
    confidence NUMERIC(5, 4) CHECK (confidence >= 0 AND confidence <= 1),
    geometry GEOMETRY(Geometry, 4326),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE TABLE IF NOT EXISTS case_evidence (
    id BIGSERIAL PRIMARY KEY,
    dump_case_id BIGINT NOT NULL REFERENCES dump_cases(id) ON DELETE CASCADE,
    image_asset_id BIGINT REFERENCES image_assets(id) ON DELETE SET NULL,
    notes TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE TABLE IF NOT EXISTS inspections (
    id BIGSERIAL PRIMARY KEY,
    dump_case_id BIGINT NOT NULL REFERENCES dump_cases(id) ON DELETE CASCADE,
    inspector_id BIGINT REFERENCES users(id),
    outcome TEXT CHECK (outcome IN ('confirmed', 'rejected', 'needs_review')),
    notes TEXT,
    inspected_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE TABLE IF NOT EXISTS cleanup_records (
    id BIGSERIAL PRIMARY KEY,
    dump_case_id BIGINT NOT NULL REFERENCES dump_cases(id) ON DELETE CASCADE,
    completed_by BIGINT REFERENCES users(id),
    completed_at TIMESTAMPTZ,
    notes TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_dump_cases_location ON dump_cases USING GIST (location);
CREATE INDEX IF NOT EXISTS idx_dump_cases_status ON dump_cases (status);
CREATE INDEX IF NOT EXISTS idx_dump_cases_created_at ON dump_cases (created_at DESC);
CREATE INDEX IF NOT EXISTS idx_detections_geometry ON detections USING GIST (geometry);
