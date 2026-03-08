from database.core import db_enabled, db_exec

def get_user(telegram_id: int):
    if not db_enabled():
        return None
    return db_exec("SELECT * FROM users WHERE telegram_id=%s", (telegram_id,), fetchone=True)

def upsert_user(telegram_id: int, language: str | None = None, ref_code: str | None = None,
                referred_by: int | None = None, profile: dict | None = None):
    if not db_enabled():
        return
    db_exec(
        """
        INSERT INTO users (telegram_id, language, ref_code, referred_by, profile_json)
        VALUES (%s, COALESCE(%s,'ru'), %s, %s, COALESCE(%s,'{}'::jsonb))
        ON CONFLICT (telegram_id) DO UPDATE
        SET language=COALESCE(EXCLUDED.language, users.language),
            ref_code=COALESCE(EXCLUDED.ref_code, users.ref_code),
            referred_by=COALESCE(EXCLUDED.referred_by, users.referred_by),
            profile_json=COALESCE(EXCLUDED.profile_json, users.profile_json);
        """,
        (telegram_id, language, ref_code, referred_by, profile),
    )
