BEGIN;

ALTER TABLE users
    ADD COLUMN IF NOT EXISTS first_name varchar(255),
    ADD COLUMN IF NOT EXISTS last_name varchar(255),
    ADD COLUMN IF NOT EXISTS fiscal_code varchar(64),
    ADD COLUMN IF NOT EXISTS phone_number varchar(64);

COMMIT;
