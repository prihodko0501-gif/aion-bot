import os
from datetime import datetime, timedelta

import requests
from flask import Flask, jsonify, request, send_from_directory
import psycopg

app = Flask(__name__)

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
API = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}" if TELEGRAM_TOKEN else None
BASE_URL = os.environ.get("BASE_URL", "https://aion-bot.onrender.com")
DATABASE_URL = os.environ.get("DATABASE_URL")


# -----------------------------
# DB
# -----------------------------

def get_db_connection():
    if not DATABASE_URL:
        raise RuntimeError("DATABASE_URL is not set")
    return psycopg.connect(DATABASE_URL)


def init_db():
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS biotime_entries (
                    id BIGSERIAL PRIMARY KEY,
                    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                    entry_date DATE NOT NULL DEFAULT CURRENT_DATE,
                    biotime NUMERIC(6, 2),
                    sleep NUMERIC(6, 2),
                    stress NUMERIC(6, 2),
                    recovery NUMERIC(6, 2),
                    pressure VARCHAR(20)
                );
            """)
        conn.commit()


# -----------------------------
# HELPERS
# -----------------------------

def clamp(value, low, high):
    return max(low, min(high, value))


def parse_float(value):
    if value in (None, "", "null"):
        return None
    try:
        return float(value)
    except Exception:
        return None


def parse_int(value):
    if value in (None, "", "null"):
        return None
    try:
        return int(value)
    except Exception:
        return None


def parse_pressure_string(value):
    if not value:
        return None, None

    value = str(value).strip().replace(" ", "")
    if "/" not in value:
        return None, None

    parts = value.split("/")
    if len(parts) != 2:
        return None, None

    sys_val = parse_int(parts[0])
    dia_val = parse_int(parts[1])
    return sys_val, dia_val


def pressure_penalty(systolic, diastolic):
    penalty = 0.0

    if systolic is None or diastolic is None:
        return 0.0

    if systolic >= 140:
        penalty += 1.2
    elif systolic >= 130:
        penalty += 0.6
    elif systolic < 100:
        penalty += 0.4

    if diastolic >= 90:
        penalty += 0.8
    elif diastolic >= 85:
        penalty += 0.4
    elif diastolic < 60:
        penalty += 0.3

    return round(penalty, 2)


def compute_biotime(sleep, stress, recovery, pressure=None):
    sleep = float(sleep or 0)
    stress = float(stress or 0)
    recovery = float(recovery or 0)

    sleep10 = sleep / 10.0
    stress10 = stress / 10.0
    recovery10 = recovery / 10.0

    systolic, diastolic = parse_pressure_string(pressure)
    p_penalty = pressure_penalty(systolic, diastolic)

    biotime = round((sleep10 * 1.2 + recovery10 * 1.2 - stress10) - p_penalty, 1)
    biotime = clamp(biotime, 0, 12)
    return biotime


def serialize_entry(row):
    if not row:
        return {
            "biotime": None,
            "sleep": None,
            "stress": None,
            "recovery": None,
            "pressure": None,
            "date": None,
            "created_at": None,
        }

    created_at = row["created_at"]
    entry_date = row["entry_date"]

    return {
        "biotime": float(row["biotime"]) if row["biotime"] is not None else None,
        "sleep": float(row["sleep"]) if row["sleep"] is not None else None,
        "stress": float(row["stress"]) if row["stress"] is not None else None,
        "recovery": float(row["recovery"]) if row["recovery"] is not None else None,
        "pressure": row["pressure"],
        "date": entry_date.isoformat() if entry_date else None,
        "created_at": created_at.isoformat() if created_at else None,
    }


def insert_entry(biotime, sleep, stress, recovery, pressure, entry_date=None, created_at=None):
    with get_db_connection() as conn:
        with conn.cursor(row_factory=psycopg.rows.dict_row) as cur:
            if entry_date is None:
                entry_date = datetime.utcnow().date()

            if created_at is None:
                cur.execute("""
                    INSERT INTO biotime_entries (
                        entry_date, biotime, sleep, stress, recovery, pressure
                    )
                    VALUES (%s, %s, %s, %s, %s, %s)
                    RETURNING id, created_at, entry_date, biotime, sleep, stress, recovery, pressure
                """, (entry_date, biotime, sleep, stress, recovery, pressure))
            else:
                cur.execute("""
                    INSERT INTO biotime_entries (
                        created_at, entry_date, biotime, sleep, stress, recovery, pressure
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    RETURNING id, created_at, entry_date, biotime, sleep, stress, recovery, pressure
                """, (created_at, entry_date, biotime, sleep, stress, recovery, pressure))

            row = cur.fetchone()
        conn.commit()
    return row


def get_latest_entry():
    with get_db_connection() as conn:
        with conn.cursor(row_factory=psycopg.rows.dict_row) as cur:
            cur.execute("""
                SELECT id, created_at, entry_date, biotime, sleep, stress, recovery, pressure
                FROM biotime_entries
                ORDER BY created_at DESC, id DESC
                LIMIT 1
            """)
            return cur.fetchone()


def get_history(days=7):
    with get_db_connection() as conn:
        with conn.cursor(row_factory=psycopg.rows.dict_row) as cur:
            cur.execute("""
                SELECT id, created_at, entry_date, biotime, sleep, stress, recovery, pressure
                FROM biotime_entries
                ORDER BY created_at DESC, id DESC
                LIMIT %s
            """, (days,))
            rows = cur.fetchall()

    rows.reverse()
    return rows


def clear_all_entries():
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("TRUNCATE TABLE biotime_entries RESTART IDENTITY;")
        conn.commit()


def seed_demo_history():
    clear_all_entries()

    base = datetime.utcnow()
    demo_rows = [
        (7.8, 88, 31, 74, "126/78"),
        (8.0, 89, 30, 75, "125/78"),
        (8.1, 90, 29, 76, "125/77"),
        (8.2, 91, 28, 76, "124/77"),
        (8.3, 91, 28, 77, "124/76"),
        (8.4, 92, 27, 78, "124/76"),
        (8.4, 92, 27, 78, "124/76"),
    ]

    for i, row in enumerate(demo_rows):
        dt = base - timedelta(days=(len(demo_rows) - 1 - i))
        entry_date = dt.date()
        created_at = dt
        insert_entry(*row, entry_date=entry_date, created_at=created_at)


# -----------------------------
# ROUTES
# -----------------------------

@app.route("/")
def home():
    return "AION is alive 🚀", 200


@app.route("/miniapp")
def miniapp():
    return send_from_directory("templates", "miniapp.html")


@app.route("/api/dashboard")
def api_dashboard():
    row = get_latest_entry()
    entry = serialize_entry(row)

    return jsonify({
        "data": {
            "biotime": entry["biotime"],
            "sleep": entry["sleep"],
            "stress": entry["stress"],
            "recovery": entry["recovery"],
            "pressure": entry["pressure"],
            "date": entry["date"],
            "created_at": entry["created_at"],
        }
    })


@app.route("/api/history")
def api_history():
    try:
        days = int(request.args.get("days", 7))
    except Exception:
        days = 7

    if days not in (7, 30, 90):
        days = 7

    rows = get_history(days)

    return jsonify({
        "days": days,
        "data": [serialize_entry(row) for row in rows]
    })


@app.route("/api/demo-seed")
def api_demo_seed():
    seed_demo_history()
    row = get_latest_entry()
    entry = serialize_entry(row)

    return jsonify({
        "status": "demo data inserted",
        "data": {
            "biotime": entry["biotime"],
            "sleep": entry["sleep"],
            "stress": entry["stress"],
            "recovery": entry["recovery"],
            "pressure": entry["pressure"],
            "date": entry["date"],
            "created_at": entry["created_at"],
        }
    })


@app.route("/api/entry", methods=["POST"])
def api_entry():
    payload = request.get_json(silent=True) or {}

    sleep = parse_float(payload.get("sleep"))
    if sleep is None:
        sleep = parse_float(payload.get("sleep_score"))

    stress = parse_float(payload.get("stress"))
    if stress is None:
        stress = parse_float(payload.get("stress_score"))

    recovery = parse_float(payload.get("recovery"))
    if recovery is None:
        recovery = parse_float(payload.get("recovery_score"))

    pressure = payload.get("pressure")

    if not pressure:
        systolic = parse_int(payload.get("systolic"))
        diastolic = parse_int(payload.get("diastolic"))
        if systolic is not None and diastolic is not None:
            pressure = f"{systolic}/{diastolic}"

    if sleep is None or stress is None or recovery is None:
        return jsonify({
            "ok": False,
            "error": "sleep, stress, recovery are required"
        }), 400

    biotime = compute_biotime(sleep, stress, recovery, pressure)
    row = insert_entry(
        biotime=biotime,
        sleep=sleep,
        stress=stress,
        recovery=recovery,
        pressure=pressure,
    )
    entry = serialize_entry(row)

    return jsonify({
        "ok": True,
        "data": {
            "biotime": entry["biotime"],
            "sleep": entry["sleep"],
            "stress": entry["stress"],
            "recovery": entry["recovery"],
            "pressure": entry["pressure"],
            "date": entry["date"],
            "created_at": entry["created_at"],
        }
    })


@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.get_json(silent=True)

    if not data:
        return {"ok": True}

    message = data.get("message")
    if not message:
        return {"ok": True}

    chat_id = message["chat"]["id"]
    text = (message.get("text") or "").strip()

    if text == "/start" and API:
        try:
            requests.post(
                f"{API}/sendMessage",
                json={
                    "chat_id": chat_id,
                    "text": "AION system online 🚀\n\nНажми кнопку ниже, чтобы открыть Mini App.",
                    "reply_markup": {
                        "inline_keyboard": [
                            [
                                {
                                    "text": "🚀 Open AION",
                                    "web_app": {
                                        "url": f"{BASE_URL}/miniapp"
                                    }
                                }
                            ],
                            [
                                {
                                    "text": "📥 Загрузить demo data",
                                    "url": f"{BASE_URL}/api/demo-seed"
                                }
                            ]
                        ]
                    }
                },
                timeout=15
            )
        except Exception as e:
            print("sendMessage error:", repr(e))

    return {"ok": True}


# -----------------------------
# START
# -----------------------------

init_db()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)