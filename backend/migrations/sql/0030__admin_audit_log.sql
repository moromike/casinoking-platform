-- Operational admin audit log for non-financial backoffice changes.
--
-- Scope:
-- - keep game/lobby configuration audit separate from financial admin_actions
-- - avoid dummy ledger/wallet fields for non-financial operations
-- - allow repeated actions to be logged independently

BEGIN;

CREATE TABLE admin_audit_log (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    admin_user_id uuid NOT NULL REFERENCES users(id),
    action_kind varchar(64) NOT NULL,
    resource_kind varchar(32) NOT NULL,
    resource_id varchar(128) NOT NULL,
    payload_json jsonb NOT NULL,
    request_fingerprint varchar(64) NOT NULL,
    created_at timestamptz NOT NULL DEFAULT now(),
    CONSTRAINT admin_audit_log_action_kind_not_blank_check
        CHECK (length(trim(action_kind)) > 0),
    CONSTRAINT admin_audit_log_resource_kind_not_blank_check
        CHECK (length(trim(resource_kind)) > 0),
    CONSTRAINT admin_audit_log_resource_id_not_blank_check
        CHECK (length(trim(resource_id)) > 0),
    CONSTRAINT admin_audit_log_request_fingerprint_length_check
        CHECK (length(request_fingerprint) = 64),
    CONSTRAINT admin_audit_log_payload_json_object_check
        CHECK (jsonb_typeof(payload_json) = 'object')
);

CREATE INDEX idx_admin_audit_log_admin
    ON admin_audit_log (admin_user_id, created_at DESC);

CREATE INDEX idx_admin_audit_log_resource
    ON admin_audit_log (resource_kind, resource_id, created_at DESC);

COMMIT;
