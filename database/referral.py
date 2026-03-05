from database.core import db_enabled, db_exec

def log_ref_event(referrer_id: int, referred_id: int, event_type: str):
    if not db_enabled():
        return
    db_exec(
        """
        INSERT INTO referral_events (referrer_id, referred_id, event_type)
        VALUES (%s,%s,%s)
        """,
        (referrer_id, referred_id, event_type),
    )
