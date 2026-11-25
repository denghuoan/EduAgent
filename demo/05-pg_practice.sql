CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
DROP TABLE IF EXISTS demo_members;
CREATE TABLE demo_members(
    id  UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    username VARCHAR(64) NOT NULL UNIQUE,
    role VARCHAR(16) NOT NULL CHECK ( role IN ('student', 'teacher', 'admin') ),
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    profile JSONB,
    create_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);


INSERT INTO  demo_members (username, role, profile)
VALUES ('alice', 'student', '{"city":"上海","tags":["java","spring"]}')
RETURNING id, username;

CREATE OR REPLACE FUNCTION demo_touch_updated_at()
RETURNS TRIGGER AS $$
    BEGIN
        NEW.updated_at = NOW();
        RETURN NEW;
    END;
    $$ LANGUAGE plpgsql;

CREATE TRIGGER trg_demo_updated_at
BEFORE UPDATE ON demo_members
FOR EACH ROW EXECUTE FUNCTION demo_touch_updated_at();


INSERT INTO demo_members (username, role)
VALUES ('alice', 'student')
ON CONFLICT (username) DO UPDATE SET role = EXCLUDED.role
RETURNING username, role;

-- JSONB查询
SELECT username,profile ->> 'city' AS city, profile -> 'tags' AS tags
FROM demo_members WHERE profile ->> 'city' = '上海';

-- 清理
DROP TABLE demo_members;
DROP FUNCTION demo_touch_updated_at();