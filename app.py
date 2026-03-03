import os
import time
import threading
import requests
import secrets
from datetime import date

from flask import Flask, request, jsonify

import psycopg2
import psycopg2.extras

app = Flask(__name__)

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
DATABASE_URL = os.environ.get("DATABASE_URL")  # Render Postgres
API_URL = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}" if TELEGRAM_TOKEN else None

# ====== MEMORY FALLBACK (если БД упала/не настроена) ======
MEM_STATE = {}  # chat_id -> {"step": str|None, "payload": dict}
MEM_UI = {}     # chat_id -> {"ui_message_id": int|None}

# ====== BUTTONS ======
BTN_BIOTIME = "🧬 BioTime"
BTN_SLEEP = "💤 Sleep"
BTN_CNS = "🧠 CNS"
BTN_RECOVERY = "🔥 Recovery"
BTN_PRESSURE = "🫀 Pressure"
BTN_INFO = "ℹ️ Info"

# ====== CALLBACKS ======
CB_BIOTIME = "biotime"
CB_SLEEP = "sleep"
CB_CNS = "cns"
CB_RECOVERY = "recovery"
CB_PRESSURE = "pressure"
CB_INFO = "info"
CB_MENU = "menu"
CB_BIOTIME_NEW = "biotime_new"

# ====== BioTime wizard steps ======
STEP_BT_SLEEP_HOURS = "bt_sleep_hours"
STEP_BT_LATENCY_MIN = "bt_latency_min"
STEP_BT_AWAKENINGS = "bt_awakenings"
STEP_BT_MORNING_FEEL = "bt_morning_feel"
STEP_BT_RHR = "bt_rhr"
STEP_BT_ENERGY = "bt_energy"
STEP_BT_PRESSURE = "bt_pressure"

WIZ_ORDER = [
    STEP_BT_SLEEP_HOURS,
    STEP_BT_LATENCY_MIN,
    STEP_BT_AWAKENINGS,
    STEP_BT_MORNING_FEEL,
    STEP_BT_RHR,
    STEP_BT_ENERGY,
    STEP_BT_PRESSURE,
]


# =========================
# DB LAYER (safe)
# =========================
def db_enabled() -> bool:
    return bool(DATABASE_URL)

def db_conn():
    # sslmode=require — безопасно и подходит для managed Postgres (Render)
    return psycopg2.connect(DATABASE_URL, sslmode="require")

def db_exec(query, params=None, fetchone=False, fetchall=False):
    """SAFE db_exec: никогда не роняет webhook."""
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

    # Одна таблица для step/ui/payload — чтобы ничего не рассинхронивалось
    db_exec("""
    CREATE TABLE IF NOT EXISTS user_state (
        telegram_id BIGINT PRIMARY KEY,
        step TEXT,
        ui_message_id BIGINT,
        payload_json JSONB NOT NULL DEFAULT '{}'::jsonb,
        updated_at TIMESTAMP NOT NULL DEFAULT NOW()
    );
    """)

    db_exec("""
    CREATE TABLE IF NOT EXISTS biotime_entries (
        id SERIAL PRIMARY KEY,
        telegram_id BIGINT NOT NULL,
        entry_date DATE NOT NULL,
        payload_json JSONB NOT NULL,
        biotime_value NUMERIC NOT NULL,
        status TEXT,
        level TEXT,
        recommendation TEXT,
        created_at TIMESTAMP NOT NULL DEFAULT NOW()
    );
    """)
    print("DB init ok")

def get_state(chat_id: int) -> dict:
    # DB -> memory fallback
    if db_enabled():
        row = db_exec("SELECT * FROM user_state WHERE telegram_id=%s", (chat_id,), fetchone=True)
        if row is not None:
            # гарантируем ключи
            row["payload_json"] = row.get("payload_json") or {}
            return row

    # memory
    return {
        "telegram_id": chat_id,
        "step": MEM_STATE.get(chat_id, {}).get("step"),
        "ui_message_id": MEM_UI.get(chat_id, {}).get("ui_message_id"),
        "payload_json": MEM_STATE.get(chat_id, {}).get("payload", {}),
    }

def set_state(chat_id: int, *, step=_ := None, ui_message_id=_ := None, payload=_ := None):
    # memory always
    if chat_id not in MEM_STATE:
        MEM_STATE[chat_id] = {"step": None, "payload": {}}
    if chat_id not in MEM_UI:
        MEM_UI[chat_id] = {"ui_message_id": None}

    if step is not None:
        MEM_STATE[chat_id]["step"] = step
    if payload is not None:
        MEM_STATE[chat_id]["payload"] = payload
    if ui_message_id is not None:
        MEM_UI[chat_id]["ui_message_id"] = ui_message_id

    # db best-effort
    if not db_enabled():
        return

    db_exec("""
        INSERT INTO user_state (telegram_id, step, ui_message_id, payload_json, updated_at)
        VALUES (%s,%s,%s,%s,NOW())
        ON CONFLICT (telegram_id) DO UPDATE
        SET
            step = COALESCE(EXCLUDED.step, user_state.step),
            ui_message_id = COALESCE(EXCLUDED.ui_message_id, user_state.ui_message_id),
            payload_json = COALESCE(EXCLUDED.payload_json, user_state.payload_json),
            updated_at = NOW();
    """, (
        chat_id,
        step,
        ui_message_id,
        psycopg2.extras.Json(payload) if payload is not None else None
    ))

def clear_wizard(chat_id: int, keep_ui: bool = True):
    st = get_state(chat_id)
    ui_mid = st.get("ui_message_id") if keep_ui else None

    MEM_STATE[chat_id] = {"step": None, "payload": {}}
    if keep_ui:
        MEM_UI[chat_id] = {"ui_message_id": ui_mid}
    else:
        MEM_UI.pop(chat_id, None)

    if not db_enabled():
        return

    if keep_ui:
        db_exec("""
            INSERT INTO user_state (telegram_id, step, ui_message_id, payload_json, updated_at)
            VALUES (%s,NULL,%s,'{}'::jsonb,NOW())
            ON CONFLICT (telegram_id) DO UPDATE
            SET step=NULL, payload_json='{}'::jsonb,
                ui_message_id=COALESCE(EXCLUDED.ui_message_id, user_state.ui_message_id),
                updated_at=NOW();
        """, (chat_id, ui_mid))
    else:
        db_exec("DELETE FROM user_state WHERE telegram_id=%s", (chat_id,))

def save_biotime_entry(chat_id: int, payload: dict, biotime: float, status: str, level: str, advice: str):
    if not db_enabled():
        return
    db_exec("""
        INSERT INTO biotime_entries
        (telegram_id, entry_date, payload_json, biotime_value, status, level, recommendation)
        VALUES (%s,%s,%s,%s,%s,%s,%s)
    """, (chat_id, date.today(), psycopg2.extras.Json(payload), biotime, status, level, advice))


# =========================
# TELEGRAM HELPERS
# =========================
def api_post(method: str, payload: dict, timeout: int = 10):
    if not API_URL:
        return None
    try:
        r = requests.post(f"{API_URL}/{method}", json=payload, timeout=timeout)
        if r.status_code == 200:
            return r.json()
        print("TG ERROR", r.status_code, r.text[:200])
    except Exception as e:
        print("TG EXC", repr(e))
    return None

def send_message(chat_id: int, text: str, reply_markup=None):
    payload = {"chat_id": chat_id, "text": text}
    if reply_markup is not None:
        payload["reply_markup"] = reply_markup
    data = api_post("sendMessage", payload)
    if data and data.get("ok"):
        return data["result"]["message_id"]
    return None

def edit_message(chat_id: int, message_id: int, text: str, reply_markup=None):
    payload = {"chat_id": chat_id, "message_id": message_id, "text": text}
    if reply_markup is not None:
        payload["reply_markup"] = reply_markup
    api_post("editMessageText", payload)

def delete_message(chat_id: int, message_id: int):
    api_post("deleteMessage", {"chat_id": chat_id, "message_id": message_id})

def try_delete_user_message(chat_id: int, message_id: int | None):
    # Чтобы цифры после ввода не оставались в чате
    if not message_id:
        return
    try:
        delete_message(chat_id, message_id)
    except Exception:
        pass

def answer_callback(callback_query_id: str):
    api_post("answerCallbackQuery", {"callback_query_id": callback_query_id})

def hide_bottom_panel_silently(chat_id: int):
    # убираем ReplyKeyboard (серую панель)
    msg_id = send_message(chat_id, "…", reply_markup={"remove_keyboard": True})
    if msg_id:
        delete_message(chat_id, msg_id)


# =========================
# UI MARKUP
# =========================
def main_menu_inline():
    return {
        "inline_keyboard": [
            [{"text": BTN_BIOTIME, "callback_data": CB_BIOTIME}],
            [{"text": BTN_SLEEP, "callback_data": CB_SLEEP},
             {"text": BTN_CNS, "callback_data": CB_CNS}],
            [{"text": BTN_RECOVERY, "callback_data": CB_RECOVERY},
             {"text": BTN_PRESSURE, "callback_data": CB_PRESSURE}],
            [{"text": BTN_INFO, "callback_data": CB_INFO}],
        ]
    }

def back_inline():
    return {"inline_keyboard": [[{"text": "⬅️ В меню", "callback_data": CB_MENU}]]}

def biotime_result_inline():
    return {
        "inline_keyboard": [
            [{"text": "🔄 Новый расчёт", "callback_data": CB_BIOTIME_NEW}],
            [{"text": "⬅️ В меню", "callback_data": CB_MENU}],
        ]
    }


# =========================
# TEXTS / BioTime LOGIC
# =========================
def start_text():
    return (
        "AION — система управления скоростью\n"
        "биологического износа, основанная на\n"
        "анализе твоей физиологии.\n\n"
        "Выберите модуль:"
    )

def info_text():
    return (
        "ℹ️ AION\n\n"
        "🧬 BioTime — интегральная оценка восстановления.\n"
        "🫀 Pressure — давление и пульс.\n"
        "💤 Sleep — сон.\n"
        "🧠 CNS — нервная система.\n"
        "🔥 Recovery — восстановление.\n\n"
        "Быстрый режим:\n"
        "/pro 7 6 8 0 0 1"
    )

def prompt(step: str):
    if step == STEP_BT_SLEEP_HOURS:
        return "🧬 BioTime — Новый расчёт\n\n1) Сон (часы)?\nНапример: 7.5"
    if step == STEP_BT_LATENCY_MIN:
        return "2) Засыпание (минут)?\nНапример: 15"
    if step == STEP_BT_AWAKENINGS:
        return "3) Пробуждения (кол-во)?\nНапример: 0"
    if step == STEP_BT_MORNING_FEEL:
        return "4) Самочувствие утром (0–10)?\nНапример: 7"
    if step == STEP_BT_RHR:
        return "5) Пульс покоя (уд/мин)?\nНапример: 58"
    if step == STEP_BT_ENERGY:
        return "6) Энергия (0–10)?\nНапример: 8"
    if step == STEP_BT_PRESSURE:
        return "7) Давление утром SYS/DIA и пульс (например: 120/80 62)\nили напиши: пропусти"
    return "…"

def clamp(x, a, b):
    return max(a, min(b, x))

def parse_float(text: str):
    return float((text or "").strip().replace(",", "."))

def parse_int(text: str):
    return int(float((text or "").strip().replace(",", ".")))

def parse_pressure(text: str):
    t = (text or "").strip().lower()
    if t in ("skip", "пропусти", "пропуск", "-", "нет"):
        return None
    parts = t.split()
    bp = parts[0]
    pulse = None
    if len(parts) >= 2:
        try:
            pulse = int(parts[1])
        except Exception:
            pulse = None
    if "/" not in bp:
        return None
    s, d = bp.split("/", 1)
    try:
        sys = int(s)
        dia = int(d)
    except Exception:
        return None
    return {"sys": sys, "dia": dia, "pulse": pulse}

def compute_biotime_from_payload(p: dict):
    sleep_h = float(p["sleep_hours"])
    latency = int(p["latency_min"])
    awaken = int(p["awakenings"])
    morning = float(p["morning_feel"])
    rhr = int(p["rhr"])
    energy = float(p["energy"])
    pressure = p.get("pressure")

    # простая MVP-модель: 0..12
    sleep_score = clamp((sleep_h / 8.0) * 10.0, 0, 10)

    stress = 0.0
    stress += clamp(latency / 6.0, 0, 5)
    stress += clamp(awaken * 1.5, 0, 5)
    stress = clamp(stress, 0, 10)

    recovery = clamp((morning * 0.55 + energy * 0.45), 0, 10)

    pressure_penalty = 0.0
    risk_penalty = 0.0

    if rhr >= 80:
        pressure_penalty += 1.5
    elif rhr >= 70:
        pressure_penalty += 1.0
    elif rhr <= 50:
        pressure_penalty += 0.3

    if pressure:
        sys = pressure["sys"]
        dia = pressure["dia"]
        if sys >= 140 or dia >= 90:
            pressure_penalty += 2.0
            risk_penalty += 1.0
        elif