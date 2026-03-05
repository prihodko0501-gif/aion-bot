import os
import psycopg2
import psycopg2.extras

DATABASE_URL = os.environ.get("DATABASE_URL")

def db_enabled() -> bool:
    return bool(DATABASE_URL)

def db_conn():
    # Render Postgres обычно требует sslmode=require
    return psycopg2.connect(DATABASE_URL, sslmode="require")

def db_exec(query, params=None, fetchone=False, fetchall=False):
    if not db_enabled():
        return None
    try:
        with db_conn() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute(query, params or ())
                if fetchone:
                    return cur.fetchone()
                if fetchall:
                    return cur.fetchall()
                return None
    except Exception as e:
        print("DB ERROR:", repr(e))
        return None

def init_db():
    if not db_enabled():
        print("DB disabled: DATABASE_URL not set. Using memory.")
        return

    # базовые таблицы
    db_exec("""
    CREATE TABLE IF NOT EXISTS aion_state (
        telegram_id BIGINT PRIMARY KEY,
        ui_message_id BIGINT,
        step TEXT,
        mode TEXT,
        payload_json JSONB NOT NULL DEFAULT '{}'::jsonb,
        updated_at TIMESTAMP NOT NULL DEFAULT NOW()
    );
    """)

    db_exec("""
    CREATE TABLE IF NOT EXISTS biotime_entries (
        id BIGSERIAL PRIMARY KEY,
        telegram_id BIGINT NOT NULL,
        entry_date DATE NOT NULL,
        payload_json JSONB NOT NULL,
        biotime_value NUMERIC NOT NULL,
        status TEXT,
        level TEXT,
        recommendation TEXT,
        protocol_training TEXT,
        protocol_sleep TEXT,
        protocol_nutrition TEXT,
        created_at TIMESTAMP NOT NULL DEFAULT NOW()
    );
    """)

    # миграции (без удаления базы)
    from database.migrations import run_migrations
    run_migrations()

    print("DB init ok")
