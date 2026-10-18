CREATE EXTENSION IF NOT EXISTS postgis;

CREATE SEQUENCE IF NOT EXISTS dump_case_code_seq;

CREATE OR REPLACE FUNCTION set_updated_at() RETURNS trigger AS $$
BEGIN
    NEW.updated_at = now();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TABLE IF NOT EXISTS users (
    id BIGSERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    email TEXT NOT NULL,
    password_hash TEXT,
    role TEXT NOT NULL DEFAULT 'uploader' CHECK (role IN ('admin', 'inspector', 'uploader')),
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE UNIQUE INDEX IF NOT EXISTS uq_users_email_lower ON users (lower(email));

CREATE TABLE IF NOT EXISTS image_assets (
    id BIGSERIAL PRIMARY KEY,
    source_type TEXT NOT NULL CHECK (source_type IN ('satellite', 'street_view', 'field_photo', 'other')),
    storage_provider TEXT NOT NULL DEFAULT 'local' CHECK (storage_provider IN ('s3', 'external', 'local')),
    storage_key TEXT UNIQUE,
    image_url TEXT,
    latitude DOUBLE PRECISION CHECK (latitude IS NULL OR latitude BETWEEN -90 AND 90),
    longitude DOUBLE PRECISION CHECK (longitude IS NULL OR longitude BETWEEN -180 AND 180),
    footprint GEOMETRY(Geometry, 4326),
    captured_at TIMESTAMPTZ,
    uploaded_by BIGINT REFERENCES users(id) ON DELETE SET NULL,
    mime_type TEXT,
    file_size_bytes BIGINT CHECK (file_size_bytes IS NULL OR file_size_bytes >= 0),
    original_filename TEXT,
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS detection_runs (
    id BIGSERIAL PRIMARY KEY,
    image_asset_id BIGINT NOT NULL REFERENCES image_assets(id) ON DELETE RESTRICT,
    model_name TEXT NOT NULL,
    model_version TEXT NOT NULL DEFAULT 'unknown',
    status TEXT NOT NULL DEFAULT 'queued' CHECK (status IN ('queued', 'running', 'completed', 'failed')),
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    error_message TEXT,
    parameters JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CHECK (completed_at IS NULL OR started_at IS NULL OR completed_at >= started_at)
);

CREATE TABLE IF NOT EXISTS dump_cases (
    id BIGSERIAL PRIMARY KEY,
    case_code TEXT NOT NULL UNIQUE DEFAULT ('DMP-' || lpad(nextval('dump_case_code_seq')::text, 6, '0')),
    location GEOGRAPHY(Point, 4326) NOT NULL,
    category TEXT,
    severity TEXT CHECK (severity IS NULL OR severity IN ('low', 'medium', 'high', 'critical')),
    risk_score NUMERIC(5, 2) CHECK (risk_score IS NULL OR risk_score BETWEEN 0 AND 100),
    status TEXT NOT NULL DEFAULT 'detected' CHECK (status IN ('detected', 'pending_verification', 'verified', 'rejected', 'needs_more_evidence', 'cleanup_assigned', 'cleaned', 'closed', 'duplicate')),
    assigned_to BIGINT REFERENCES users(id) ON DELETE SET NULL,
    reported_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    description TEXT,
    source TEXT NOT NULL DEFAULT 'manual',
    duplicate_of_case_id BIGINT REFERENCES dump_cases(id) ON DELETE RESTRICT
);

CREATE TABLE IF NOT EXISTS detections (
    id BIGSERIAL PRIMARY KEY,
    detection_run_id BIGINT NOT NULL REFERENCES detection_runs(id) ON DELETE RESTRICT,
    dump_case_id BIGINT REFERENCES dump_cases(id) ON DELETE SET NULL,
    class_name TEXT NOT NULL,
    confidence NUMERIC(5, 4) NOT NULL CHECK (confidence BETWEEN 0 AND 1),
    bounding_box JSONB CHECK (bounding_box IS NULL OR jsonb_typeof(bounding_box) = 'object'),
    area_estimate NUMERIC CHECK (area_estimate IS NULL OR area_estimate >= 0),
    geometry GEOMETRY(Geometry, 4326),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS case_evidence (
    id BIGSERIAL PRIMARY KEY,
    dump_case_id BIGINT NOT NULL REFERENCES dump_cases(id) ON DELETE RESTRICT,
    image_asset_id BIGINT NOT NULL REFERENCES image_assets(id) ON DELETE RESTRICT,
    evidence_type TEXT NOT NULL CHECK (evidence_type IN ('satellite', 'street_view', 'field_photo', 'document', 'other')),
    notes TEXT,
    added_by BIGINT REFERENCES users(id) ON DELETE SET NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS inspections (
    id BIGSERIAL PRIMARY KEY,
    dump_case_id BIGINT NOT NULL REFERENCES dump_cases(id) ON DELETE RESTRICT,
    inspector_id BIGINT NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
    decision TEXT NOT NULL CHECK (decision IN ('confirmed', 'rejected', 'needs_more_evidence')),
    confirmed_category TEXT,
    confirmed_severity TEXT CHECK (confirmed_severity IS NULL OR confirmed_severity IN ('low', 'medium', 'high', 'critical')),
    notes TEXT,
    inspected_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS cleanup_records (
    id BIGSERIAL PRIMARY KEY,
    dump_case_id BIGINT NOT NULL REFERENCES dump_cases(id) ON DELETE RESTRICT,
    assigned_team TEXT,
    status TEXT NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'in_progress', 'completed', 'cancelled')),
    assigned_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    notes TEXT,
    before_evidence_id BIGINT REFERENCES case_evidence(id) ON DELETE RESTRICT,
    after_evidence_id BIGINT REFERENCES case_evidence(id) ON DELETE RESTRICT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CHECK (completed_at IS NULL OR assigned_at IS NULL OR completed_at >= assigned_at)
);

DROP TRIGGER IF EXISTS trg_users_updated_at ON users;
CREATE TRIGGER trg_users_updated_at BEFORE UPDATE ON users FOR EACH ROW EXECUTE FUNCTION set_updated_at();
DROP TRIGGER IF EXISTS trg_dump_cases_updated_at ON dump_cases;
CREATE TRIGGER trg_dump_cases_updated_at BEFORE UPDATE ON dump_cases FOR EACH ROW EXECUTE FUNCTION set_updated_at();
DROP TRIGGER IF EXISTS trg_cleanup_records_updated_at ON cleanup_records;
CREATE TRIGGER trg_cleanup_records_updated_at BEFORE UPDATE ON cleanup_records FOR EACH ROW EXECUTE FUNCTION set_updated_at();

CREATE INDEX IF NOT EXISTS idx_image_assets_uploaded_by ON image_assets (uploaded_by);
CREATE INDEX IF NOT EXISTS idx_image_assets_source_type ON image_assets (source_type);
CREATE INDEX IF NOT EXISTS idx_image_assets_captured_at ON image_assets (captured_at DESC);
CREATE INDEX IF NOT EXISTS idx_image_assets_footprint ON image_assets USING GIST (footprint);
CREATE INDEX IF NOT EXISTS idx_detection_runs_image_asset_id ON detection_runs (image_asset_id);
CREATE INDEX IF NOT EXISTS idx_detection_runs_status ON detection_runs (status);
CREATE INDEX IF NOT EXISTS idx_dump_cases_location ON dump_cases USING GIST (location);
CREATE INDEX IF NOT EXISTS idx_dump_cases_status ON dump_cases (status);
CREATE INDEX IF NOT EXISTS idx_dump_cases_severity ON dump_cases (severity);
CREATE INDEX IF NOT EXISTS idx_dump_cases_assigned_to ON dump_cases (assigned_to);
CREATE INDEX IF NOT EXISTS idx_dump_cases_created_at ON dump_cases (created_at DESC);
CREATE INDEX IF NOT EXISTS idx_detections_run_id ON detections (detection_run_id);
CREATE INDEX IF NOT EXISTS idx_detections_case_id ON detections (dump_case_id);
CREATE INDEX IF NOT EXISTS idx_detections_geometry ON detections USING GIST (geometry);
CREATE INDEX IF NOT EXISTS idx_case_evidence_case_id ON case_evidence (dump_case_id);
CREATE INDEX IF NOT EXISTS idx_case_evidence_image_id ON case_evidence (image_asset_id);
CREATE INDEX IF NOT EXISTS idx_inspections_case_id ON inspections (dump_case_id);
CREATE INDEX IF NOT EXISTS idx_inspections_inspector_id ON inspections (inspector_id);
CREATE INDEX IF NOT EXISTS idx_cleanup_records_case_id ON cleanup_records (dump_case_id);
CREATE INDEX IF NOT EXISTS idx_cleanup_records_status ON cleanup_records (status);
