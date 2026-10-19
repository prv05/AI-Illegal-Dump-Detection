ALTER TABLE dump_cases
    ADD COLUMN IF NOT EXISTS submitted_by BIGINT REFERENCES users(id) ON DELETE SET NULL;

CREATE INDEX IF NOT EXISTS idx_dump_cases_submitted_by ON dump_cases (submitted_by);

UPDATE dump_cases
SET submitted_by = image_owner.uploaded_by
FROM (
    SELECT ce.dump_case_id, MIN(ia.uploaded_by) AS uploaded_by
    FROM case_evidence ce
    JOIN image_assets ia ON ia.id = ce.image_asset_id
    WHERE ia.uploaded_by IS NOT NULL
    GROUP BY ce.dump_case_id
) AS image_owner
WHERE dump_cases.submitted_by IS NULL
  AND image_owner.uploaded_by IS NOT NULL;
