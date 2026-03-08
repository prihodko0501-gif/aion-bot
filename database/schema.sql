CREATE TABLE IF NOT EXISTS users (
    id BIGSERIAL PRIMARY KEY,
    telegram_user_id BIGINT UNIQUE NOT NULL,
    username TEXT,
    first_name TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS biotime_entries (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT,
    entry_date DATE,
    sleep_hours NUMERIC,
    sleep_quality NUMERIC,
    resting_hr INTEGER,
    systolic INTEGER,
    diastolic INTEGER,
    pulse INTEGER,
    energy NUMERIC,
    stress_self NUMERIC,
    sleep_score NUMERIC,
    stress_score NUMERIC,
    pressure_penalty NUMERIC,
    recovery_score NUMERIC,
    core_biotime NUMERIC,
    final_biotime NUMERIC,
    aion_index INTEGER,
    zone TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS aion_state (
    user_id BIGINT PRIMARY KEY,
    ui_message_id BIGINT,
    step TEXT,
    mode TEXT,
    payload_json JSONB,
    updated_at TIMESTAMP DEFAULT NOW()
);