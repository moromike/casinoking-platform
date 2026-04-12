BEGIN;

CREATE TABLE IF NOT EXISTS access_logs (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id         UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    user_email      TEXT NOT NULL,
    user_role       TEXT NOT NULL,
    ip_address      TEXT,
    action          TEXT NOT NULL DEFAULT 'login',
    logged_at       TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_access_logs_user_id   ON access_logs(user_id);
CREATE INDEX IF NOT EXISTS idx_access_logs_user_role  ON access_logs(user_role);
CREATE INDEX IF NOT EXISTS idx_access_logs_logged_at  ON access_logs(logged_at DESC);

COMMIT;
