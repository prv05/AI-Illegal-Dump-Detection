CREATE TABLE IF NOT EXISTS notifications (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    title TEXT NOT NULL,
    message TEXT NOT NULL,
    notification_type TEXT NOT NULL DEFAULT 'system',
    related_case_id BIGINT REFERENCES dump_cases(id) ON DELETE SET NULL,
    is_read BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    read_at TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS idx_notifications_user_created ON notifications (user_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_notifications_user_unread ON notifications (user_id, is_read);

CREATE OR REPLACE FUNCTION notify_case_status_change() RETURNS trigger AS $$
BEGIN
    IF NEW.submitted_by IS NOT NULL AND OLD.status IS DISTINCT FROM NEW.status THEN
        INSERT INTO notifications (user_id, title, message, notification_type, related_case_id)
        VALUES (
            NEW.submitted_by,
            'Report status updated',
            'Your report ' || NEW.case_code || ' is now ' || replace(NEW.status, '_', ' ') || '.',
            'case_update',
            NEW.id
        );
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_notify_case_status_change ON dump_cases;
CREATE TRIGGER trg_notify_case_status_change
AFTER UPDATE OF status ON dump_cases
FOR EACH ROW EXECUTE FUNCTION notify_case_status_change();
