from database.core import db_exec, db_enabled

def run_migrations():
    if not db_enabled():
        return

    db_exec("ALTER TABLE aion_state ADD COLUMN IF NOT EXISTS mode TEXT;")
    db_exec("ALTER TABLE aion_state ADD COLUMN IF NOT EXISTS payload_json JSONB NOT NULL DEFAULT '{}'::jsonb;")