import os
from datetime import datetime, date
from typing import Optional

import requests
import psycopg2
from psycopg2.extras import RealDictCursor
from flask import Flask, request, send_from_directory, render_template, jsonify

app = Flask(__name__)

TOKEN = os.environ.get("TELEGRAM_TOKEN")
API = f"https://api.telegram.org/bot{TOKEN}" if TOKEN else None

IMAGE_URL = "https://raw.githubusercontent.com/prihodko0501-gif/aion-bot/main/563CC010-50CF-4E76-9C55-A3CEA18351D9.png"
DATABASE_URL = os.environ.get("DATABASE_URL")


# =========================
# DB
# =========================
def get_conn():
    if not DATABASE_URL:
        raise RuntimeError("DATABASE_URL is not set")
    return psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)


def init_db():
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS biotime_entries (
                    id SERIAL PRIMARY KEY,
                    user_id BIGINT NOT NULL,
                    entry_date DATE NOT NULL DEFAULT CURRENT_DATE,

                    sleep_score NUMERIC(10,2),
                    stress_score NUMERIC(10,2),
                    recovery_score NUMERIC(10,2),

                    systolic INTEGER,
                    diastolic INTEGER,

                    sleep_duration_minutes INTEGER,
                    sleep_latency_minutes INTEGER,
                    sleep_stability NUMERIC(10,2),

                    pressure_penalty NUMERIC(10,2) DEFAULT 0,
                    drop_penalty NUMERIC(10,2) DEFAULT 0,
                    risk_penalty NUMERIC(10,2) DEFAULT 0,

                    biotime NUMERIC(10,2),

                    created_at TIMESTAMP NOT NULL DEFAULT NOW()
                );
            """)

            cur.execute("""
                CREATE INDEX IF NOT EXISTS idx_biotime_entries_user_date
                ON biotime_entries (user_id, entry_date DESC, created_at DESC);
            """)

        conn.commit()


# =========================
# AION FORMULA
# =========================
def clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


def calc_pressure_penalty(systolic: Optional[int], diastolic: Optional[int]) -> float:
    if systolic is None or diastolic is None:
        return 0.0

    penalty = 0.0

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


def calc_biotime(
    sleep_score: Optional[float],
    recovery_score: Optional[float],
    stress_score: Optional[float],
    systolic: Optional[int],
    diastolic: Optional[int],
    drop_penalty: float = 0.0,
    risk_penalty: float = 0.0,
):
    sleep_score = float(sleep_score or 0)
    recovery_score = float(recovery_score or 0)
    stress_score = float(stress_score or 0)

    # переводим проценты 0-100 в шкалу 0-10
    sleep10 = sleep_score / 10.0
    recovery10 = recovery_score / 10.0
    stress10 = stress_score / 10.0

    pressure_penalty = calc_pressure_penalty(systolic, diastolic)

    biotime = round(
        (sleep10 * 1.2 + recovery10 * 1.2 - stress10)
        - float(pressure_penalty)
        - float(drop_penalty or 0)
        - float(risk_penalty or 0),
        1
    )

    biotime = clamp(biotime, 0, 12)

    return {
        "biotime": biotime,
        "pressure_penalty": round(pressure_penalty, 2),
        "drop_penalty": round(float(drop_penalty or 0), 2),
        "risk_penalty": round(float(risk_penalty or 0), 2),
    }


# =========================
# HELPERS
# =========================
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


def fetchone(query, params=None):
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(query, params or ())
            return cur.fetchone()


def fetchall(query, params=None):
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(query, params or ())
            return cur.fetchall()


# =========================
# ROUTES
# =========================
@app.route("/")
def home():
    return "AION is alive 🚀", 200


@app.route("/miniapp")
def miniapp():
    return render_template("miniapp.html")


@app.route("/app")
def mini_app():
    return send_from_directory("webapp", "index.html")


@app.route("/api/dashboard")
def api_dashboard():
    user_id = request.args.get("user_id", default=1, type=int)

    row = fetchone("""
        SELECT
            user_id,
            entry_date,
            biotime,
            sleep_score,
            stress_score,
            recovery_score,
            systolic,
            diastolic
        FROM biotime_entries
        WHERE user_id = %s
        ORDER BY entry_date DESC, created_at DESC
        LIMIT 1
    """, (user_id,))

    if not row:
        return jsonify({
            "data": {
                "entry_date": None,
                "biotime": None,
                "sleep": None,
                "stress": None,
                "recovery": None,
                "pressure": None
            }
        })

    pressure = None
    if row["systolic"] is not None and row["diastolic"] is not None:
        pressure = f'{row["systolic"]}/{row["diastolic"]}'

    return jsonify({
        "data": {
            "entry_date": str(row["entry_date"]) if row["entry_date"] else None,
            "biotime": float(row["biotime"]) if row["biotime"] is not None else None,
            "sleep": float(row["sleep_score"]) if row["sleep_score"] is not None else None,
            "stress": float(row["stress_score"]) if row["stress_score"] is not None else None,
            "recovery": float(row["recovery_score"]) if row["recovery_score"] is not None else None,
            "pressure": pressure
        }
    })


@app.route("/api/history")
def api_history():
    user_id = request.args.get("user_id", default=1, type=int)
    days = request.args.get("days", default=7, type=int)

    if days not in (7, 30, 90):
        days = 7

    rows = fetchall("""
        SELECT
            entry_date,
            biotime,
            sleep_score,
            stress_score,
            recovery_score
        FROM biotime_entries
        WHERE user_id = %s
          AND entry_date >= CURRENT_DATE - (%s::int - 1)
        ORDER BY entry_date ASC, created_at ASC
    """, (user_id, days))

    return jsonify({
        "data": [
            {
                "date": str(r["entry_date"]) if r["entry_date"] else None,
                "biotime": float(r["biotime"]) if r["biotime"] is not None else None,
                "sleep": float(r["sleep_score"]) if r["sleep_score"] is not None else None,
                "stress": float(r["stress_score"]) if r["stress_score"] is not None else None,
                "recovery": float(r["recovery_score"]) if r["recovery_score"] is not None else None,
            }
            for r in rows
        ]
    })


@app.route("/api/sleep")
def api_sleep():
    user_id = request.args.get("user_id", default=1, type=int)

    row = fetchone("""
        SELECT
            entry_date,
            sleep_score,
            sleep_duration_minutes,
            sleep_latency_minutes,
            sleep_stability
        FROM biotime_entries
        WHERE user_id = %s
        ORDER BY entry_date DESC, created_at DESC
        LIMIT 1
    """, (user_id,))

    if not row:
        return jsonify({"data": None})

    duration = None
    if row["sleep_duration_minutes"] is not None:
        h = int(row["sleep_duration_minutes"]) // 60
        m = int(row["sleep_duration_minutes"]) % 60
        duration = f"{h}h {m}m"

    return jsonify({
        "data": {
            "date": str(row["entry_date"]) if row["entry_date"] else None,
            "score": float(row["sleep_score"]) if row["sleep_score"] is not None else None,
            "duration": duration,
            "latency_minutes": row["sleep_latency_minutes"],
            "stability": float(row["sleep_stability"]) if row["sleep_stability"] is not None else None,
        }
    })


@app.route("/api/entry", methods=["POST"])
def api_entry():
    payload = request.get_json(silent=True) or {}

    user_id = parse_int(payload.get("user_id")) or 1
    entry_date_raw = payload.get("entry_date")
    entry_date = entry_date_raw or str(date.today())

    sleep_score = parse_float(payload.get("sleep_score"))
    stress_score = parse_float(payload.get("stress_score"))
    recovery_score = parse_float(payload.get("recovery_score"))

    systolic = parse_int(payload.get("systolic"))
    diastolic = parse_int(payload.get("diastolic"))

    sleep_duration_minutes = parse_int(payload.get("sleep_duration_minutes"))
    sleep_latency_minutes = parse_int(payload.get("sleep_latency_minutes"))
    sleep_stability = parse_float(payload.get("sleep_stability"))

    drop_penalty = parse_float(payload.get("drop_penalty")) or 0.0
    risk_penalty = parse_float(payload.get("risk_penalty")) or 0.0

    calc = calc_biotime(
        sleep_score=sleep_score,
        recovery_score=recovery_score,
        stress_score=stress_score,
        systolic=systolic,
        diastolic=diastolic,
        drop_penalty=drop_penalty,
        risk_penalty=risk_penalty,
    )

    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO biotime_entries (
                    user_id,
                    entry_date,
                    sleep_score,
                    stress_score,
                    recovery_score,
                    systolic,
                    diastolic,
                    sleep_duration_minutes,
                    sleep_latency_minutes,
                    sleep_stability,
                    pressure_penalty,
                    drop_penalty,
                    risk_penalty,
                    biotime
                )
                VALUES (
                    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                )
                RETURNING id, user_id, entry_date, biotime
            """, (
                user_id,
                entry_date,
                sleep_score,
                stress_score,
                recovery_score,
                systolic,
                diastolic,
                sleep_duration_minutes,
                sleep_latency_minutes,
                sleep_stability,
                calc["pressure_penalty"],
                calc["drop_penalty"],
                calc["risk_penalty"],
                calc["biotime"],
            ))
            saved = cur.fetchone()
        conn.commit()

    return jsonify({
        "ok": True,
        "saved": {
            "id": saved["id"],
            "user_id": saved["user_id"],
            "entry_date": str(saved["entry_date"]),
            "biotime": float(saved["biotime"]),
        },
        "formula": calc
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
                f"{API}/sendPhoto",
                json={
                    "chat_id": chat_id,
                    "photo": IMAGE_URL,
                    "caption": "UPGRADE SYSTEM\n\nMini App: https://aion-bot.onrender.com/miniapp"
                },
                timeout=15
            )
        except Exception as e:
            print("sendPhoto error:", repr(e))

    return {"ok": True}


# =========================
# START
# =========================
init_db()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)