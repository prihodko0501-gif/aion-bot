import io
import csv
from datetime import date, datetime, timedelta
import psycopg2.extras

from database.core import db_enabled, db_exec

def save_biotime_entry(
    chat_id: int,
    payload: dict,
    biotime: float,
    status: str,
    level: str,
    advice: str,
    p_train: str,
    p_sleep: str,
    p_nutri: str,
):
    if not db_enabled():
        return
    db_exec(
        """
        INSERT INTO biotime_entries
        (telegram_id, entry_date, payload_json, biotime_value, status, level, recommendation,
         protocol_training, protocol_sleep, protocol_nutrition)
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
        """,
        (
            chat_id,
            date.today(),
            psycopg2.extras.Json(payload),
            biotime,
            status,
            level,
            advice,
            p_train,
            p_sleep,
            p_nutri,
        ),
    )

def fetch_last_entry(chat_id: int):
    if not db_enabled():
        return None
    return db_exec(
        """
        SELECT *
        FROM biotime_entries
        WHERE telegram_id=%s
        ORDER BY created_at DESC
        LIMIT 1
        """,
        (chat_id,),
        fetchone=True,
    )

def fetch_history(chat_id: int, days: int = 14):
    if not db_enabled():
        return []
    since = datetime.utcnow() - timedelta(days=days)
    rows = db_exec(
        """
        SELECT created_at, entry_date, biotime_value, status, level, recommendation
        FROM biotime_entries
        WHERE telegram_id=%s AND created_at >= %s
        ORDER BY created_at DESC
        """,
        (chat_id, since),
        fetchall=True,
    )
    return rows or []

def fetch_history_limit(chat_id: int, limit: int = 60):
    if not db_enabled():
        return []
    rows = db_exec(
        """
        SELECT created_at, entry_date, biotime_value, status, level, recommendation,
               protocol_training, protocol_sleep, protocol_nutrition
        FROM biotime_entries
        WHERE telegram_id=%s
        ORDER BY created_at DESC
        LIMIT %s
        """,
        (chat_id, limit),
        fetchall=True,
    )
    return rows or []

def build_csv_bytes(rows_desc: list[dict]) -> bytes:
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "created_at",
        "entry_date",
        "biotime_value",
        "status",
        "level",
        "recommendation",
        "protocol_training",
        "protocol_sleep",
        "protocol_nutrition",
    ])
    for r in rows_desc:
        writer.writerow([
            r.get("created_at"),
            r.get("entry_date"),
            r.get("biotime_value"),
            r.get("status"),
            r.get("level"),
            r.get("recommendation"),
            r.get("protocol_training"),
            r.get("protocol_sleep"),
            r.get("protocol_nutrition"),
        ])
    return output.getvalue().encode("utf-8")
