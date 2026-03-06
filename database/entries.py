from datetime import datetime, timedelta
from .core import get_connection


def ensure_table():
    conn = get_connection()
    if not conn:
        return

    cur = conn.cursor()

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS biotime_entries (
            id SERIAL PRIMARY KEY,
            user_id BIGINT,
            biotime FLOAT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
    )

    conn.commit()
    cur.close()
    conn.close()


def save_biotime_entry(
    user_id: int,
    payload: dict,
    biotime: float,
    status: str = "",
    level: str = "",
    advice: str = "",
    p_train: str = "",
    p_sleep: str = "",
    p_nutri: str = "",
):
    ensure_table()

    conn = get_connection()
    if not conn:
        return

    cur = conn.cursor()

    cur.execute(
        """
        INSERT INTO biotime_entries (user_id, biotime)
        VALUES (%s, %s)
        """,
        (user_id, biotime)
    )

    conn.commit()
    cur.close()
    conn.close()


def fetch_history(user_id: int, days: int = 7):
    ensure_table()

    conn = get_connection()
    if not conn:
        return []

    cur = conn.cursor()
    since = datetime.utcnow() - timedelta(days=days)

    cur.execute(
        """
        SELECT created_at, biotime
        FROM biotime_entries
        WHERE user_id = %s
          AND created_at >= %s
        ORDER BY created_at DESC
        """,
        (user_id, since)
    )

    rows = cur.fetchall()

    cur.close()
    conn.close()

    return rows or []


def fetch_history_limit(user_id: int, limit: int = 30):
    ensure_table()

    conn = get_connection()
    if not conn:
        return []

    cur = conn.cursor()

    cur.execute(
        """
        SELECT created_at, biotime
        FROM biotime_entries
        WHERE user_id = %s
        ORDER BY created_at DESC
        LIMIT %s
        """,
        (user_id, limit)
    )

    rows = cur.fetchall()

    cur.close()
    conn.close()

    return rows or []


def fetch_last_entry(user_id: int):
    rows = fetch_history_limit(user_id, limit=1)
    if not rows:
        return None
    return rows[0]