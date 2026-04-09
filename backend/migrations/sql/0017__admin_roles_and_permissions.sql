BEGIN;

-- Create admin_profiles table linking to users with role='admin'
CREATE TABLE admin_profiles (
    user_id uuid PRIMARY KEY REFERENCES users(id),
    is_superadmin boolean NOT NULL DEFAULT false,
    areas text[] NOT NULL DEFAULT '{}',
    created_at timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX idx_admin_profiles_user_id ON admin_profiles (user_id);

-- Backfill: insert admin_profiles for all existing admin users
-- All existing admins get is_superadmin=true for retrocompatibility
INSERT INTO admin_profiles (user_id, is_superadmin, areas, created_at)
SELECT id, true, '{}', now()
FROM users
WHERE role = 'admin'
ON CONFLICT (user_id) DO NOTHING;

COMMIT;
