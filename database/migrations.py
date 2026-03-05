from database.core import db_exec, db_enabled

def run_migrations():
    if not db_enabled():
        return

    # safety: если старые таблицы — добавляем недостающие колонки
    db_exec("ALTER TABLE aion_state ADD COLUMN IF NOT EXISTS mode TEXT;")
    db_exec("ALTER TABLE aion_state ADD COLUMN IF NOT EXISTS payload_json JSONB NOT NULL DEFAULT '{}'::jsonb;")

    # users: язык/рефералка/профиль
    db_exec("""
    CREATE TABLE IF NOT EXISTS users (
        telegram_id BIGINT PRIMARY KEY,
        language TEXT DEFAULT 'ru',
        ref_code TEXT,
        referred_by BIGINT,
        profile_json JSONB NOT NULL DEFAULT '{}'::jsonb,
        created_at TIMESTAMP NOT NULL DEFAULT NOW()
    );
    """)

    # referral events
    db_exec("""
    CREATE TABLE IF NOT EXISTS referral_events (
        id BIGSERIAL PRIMARY KEY,
        referrer_id BIGINT NOT NULL,
        referred_id BIGINT NOT NULL,
        event_type TEXT NOT NULL,
        created_at TIMESTAMP NOT NULL DEFAULT NOW()
    );
    """)
