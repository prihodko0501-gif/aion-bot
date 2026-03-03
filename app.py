import os
import time
import threading
import requests
from datetime import date

from flask import Flask, request, jsonify

import psycopg2
import psycopg2.extras

app = Flask(__name__)

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
API_URL = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}" if TELEGRAM_TOKEN else None
DATABASE_URL = os.environ.get("DATABASE_URL")

# ====== BUTTONS / CALLBACKS ======
BTN_BIOTIME = "🧬 BioTime"
BTN_SLEEP = "💤 Sleep"
BTN_CNS = "🧠 CNS"
BTN_RECOVERY = "🔥 Recovery"
BTN_PRESSURE = "🫀 Pressure"
BTN_INFO = "ℹ️ Info"

CB_BIOTIME = "biotime"
CB_SLEEP = "sleep"
CB_CNS = "cns"
CB_RECOVERY = "recovery"
CB_PRESSURE = "pressure"
CB_INFO = "info"
CB_MENU = "menu"
CB_BIOTIME_NEW = "biotime_new"

# ====== Wizard steps ======
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
# DB
# =========================
def db_enabled() -> bool:
    return bool(DATABASE_URL)

def db_conn():
    return psycopg2.connect(DATABASE_URL, sslmode="require")

def db_ok() -> tuple[bool, str]:
    """Жёсткая проверка БД, чтобы не было 'тихих' падений."""
    if not db_enabled():
        return (False, "DATABASE_URL is empty")
    try:
        with db_conn() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT 1;")
                cur.fetchone()
        return (True, "ok")
    except Exception as e:
        return (False, repr(e))

def db_exec(query, params=None, fetchone=False, fetchall=False):
    if not db_enabled():
        raise RuntimeError("DB disabled")
    with db_conn() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(query, params or ())
            if fetchone:
                return cur.fetchone()
            if fetchall:
                return cur.fetchall()
            return None

def init_db():
    ok, msg = db_ok()
    print("DB CHECK:", ok, msg)
    if not ok:
        return

    db_exec("""
    CREATE TABLE IF NOT EXISTS user_state (
        telegram_id BIGINT PRIMARY KEY,
        step TEXT,
        ui_message_id BIGINT,
        payload_json JSONB,
        updated_at TIMESTAMP NOT NULL DEFAULT NOW()
    );
    """)
    db_exec("""
    CREATE TABLE IF NOT EXISTS biotime_entries (
        id SERIAL PRIMARY KEY,
        telegram_id BIGINT NOT NULL,
        entry_date DATE NOT NULL,
        payload_json JSONB,
        biotime_value NUMERIC NOT NULL,
        status TEXT,
        level TEXT,
        recommendation TEXT,
        created_at TIMESTAMP NOT NULL DEFAULT NOW()
    );
    """)
    print("DB init ok")

def get_state(chat_id: int):
    ok, msg = db_ok()
    if not ok:
        # если БД умерла — возвращаем "пусто" (и НЕ рисуем меню спамом)
        return {"step": None, "ui_message_id": None, "payload": {}, "db_ok": False, "db_msg": msg}

    row = db_exec("SELECT * FROM user_state WHERE telegram_id=%s", (chat_id,), fetchone=True)
    if not row:
        return {"step": None, "ui_message_id": None, "payload": {}, "db_ok": True, "db_msg": "ok"}
    return {
        "step": row.get("step"),
        "ui_message_id": row.get("ui_message_id"),
        "payload": row.get("payload_json") or {},
        "db_ok": True,
        "db_msg": "ok",
    }

def set_state(chat_id: int, step, ui_message_id, payload: dict):
    ok, msg = db_ok()
    if not ok:
        raise RuntimeError(f"DB down: {msg}")

    db_exec("""
        INSERT INTO user_state (telegram_id, step, ui_message_id, payload_json, updated_at)
        VALUES (%s,%s,%s,%s,NOW())
        ON CONFLICT (telegram_id) DO UPDATE
        SET step=EXCLUDED.step,
            ui_message_id=EXCLUDED.ui_message_id,
            payload_json=EXCLUDED.payload_json,
            updated_at=NOW();
    """, (chat_id, step, ui_message_id, psycopg2.extras.Json(payload or {})))

def clear_step_keep_ui(chat_id: int):
    st = get_state(chat_id)
    if not st["db_ok"]:
        return
    set_state(chat_id, step=None, ui_message_id=st["ui_message_id"], payload={})

def save_biotime_entry(chat_id: int, payload: dict, biotime: float, status: str, level: str, advice: str):
    ok, _ = db_ok()
    if not ok:
        return
    db_exec("""
        INSERT INTO biotime_entries
        (telegram_id, entry_date, payload_json, biotime_value, status, level, recommendation)
        VALUES (%s,%s,%s,%s,%s,%s,%s)
    """, (chat_id, date.today(), psycopg2.extras.Json(payload), biotime, status, level, advice))

# =========================
# Telegram API
# =========================
def api_post(method: str, payload: dict, timeout: int = 10):
    if not API_URL:
        return None
    try:
        r = requests.post(f"{API_URL}/{method}", json=payload, timeout=timeout)
        if r.status_code == 200:
            return r.json()
        print("TG ERROR", r.status_code, r.text[:250])
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
    if not message_id:
        return
    try:
        delete_message(chat_id, message_id)
    except Exception:
        pass

def answer_callback(callback_query_id: str):
    api_post("answerCallbackQuery", {"callback_query_id": callback_query_id})

# =========================
# UI
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
        "Выбирай модуль в меню."
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
    if not parts:
        return None
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
        elif sys >= 130 or dia >= 85:
            pressure_penalty += 1.0
        elif sys < 100 or dia < 65:
            pressure_penalty += 0.7

    drop_penalty = 0.0
    if sleep_h < 6:
        drop_penalty += 1.0
    if awaken >= 3:
        drop_penalty += 0.5

    biotime = round(
        (sleep_score * 0.6 + recovery * 0.8 - stress * 0.7) + 6.0
        - pressure_penalty - drop_penalty - risk_penalty,
        1
    )
    return clamp(biotime, 0.0, 12.0)

def classify_biotime(biotime: float):
    if biotime < 4:
        return ("ALERT MODE", "🔴 Высокая", "Разгрузка / восстановление")
    if biotime < 8:
        return ("CAUTION", "🟠 Средняя", "Снизить объём")
    if biotime <= 11:
        return ("NORMAL", "🟡 Норма", "Без форсирования")
    return ("OPTIMAL", "🟢 Оптимум", "Работай по плану")

def result_block(biotime: float):
    filled = int(round(biotime))
    bar = "▰" * filled + "▱" * (12 - filled)
    status, level, advice = classify_biotime(biotime)
    return (
        "━━━━━━━━━━━━━━━━━━\n"
        "🧬 BioTime\n\n"
        f"Индекс: {biotime} / 12\n"
        f"{bar}\n\n"
        f"Статус: {status}\n"
        f"Уровень: {level}\n\n"
        f"Что делать сегодня: {advice}\n"
        "━━━━━━━━━━━━━━━━━━"
    )

def next_step(step: str):
    try:
        i = WIZ_ORDER.index(step)
        return WIZ_ORDER[i + 1] if i + 1 < len(WIZ_ORDER) else None
    except Exception:
        return None

def ensure_ui(chat_id: int):
    st = get_state(chat_id)
    if not st["db_ok"]:
        # вместо спама меню — говорим честно
        send_message(chat_id, f"⚠️ БД недоступна: {st['db_msg']}\n\nПочини Postgres/URL, и всё заработает.")
        return None

    mid = st["ui_message_id"]
    if mid:
        edit_message(chat_id, mid, start_text(), main_menu_inline())
        return mid

    mid = send_message(chat_id, start_text(), main_menu_inline())
    set_state(chat_id, step=None, ui_message_id=mid, payload={})
    return mid

def start_biotime_wizard(chat_id: int, message_id: int):
    set_state(chat_id, step=STEP_BT_SLEEP_HOURS, ui_message_id=message_id, payload={})
    edit_message(chat_id, message_id, prompt(STEP_BT_SLEEP_HOURS), back_inline())

def core_animation_async(chat_id: int, mid: int, biotime: float):
    def run():
        steps = [
            ("🧬 BioTime\n\nИнициализация...", biotime_result_inline()),
            ("🧠 Анализ данных…\n▰▱▱▱▱", biotime_result_inline()),
            ("🫀 Оценка нагрузки…\n▰▰▰▱▱", biotime_result_inline()),
            ("🔥 Сбор интеграла…\n▰▰▰▰▰", biotime_result_inline()),
        ]
        for txt, mk in steps:
            edit_message(chat_id, mid, txt, mk)
            time.sleep(0.25)
        edit_message(chat_id, mid, result_block(biotime), biotime_result_inline())
    threading.Thread(target=run, daemon=True).start()

# =========================
# ROUTES
# =========================
@app.get("/")
def home():
    ok, msg = db_ok()
    return f"AION is alive 🚀 | db_ok={ok} | {msg}", 200

@app.post("/webhook")
def webhook():
    update = request.get_json(silent=True) or {}

    # ==== CALLBACKS ====
    if "callback_query" in update:
        cq = update["callback_query"]
        callback_query_id = cq.get("id")
        data = cq.get("data")

        msg = cq.get("message") or {}
        chat_id = (msg.get("chat") or {}).get("id")
        message_id = msg.get("message_id")

        if callback_query_id:
            answer_callback(callback_query_id)

        if not chat_id or not message_id:
            return jsonify({"ok": True})

        # фиксируем ui_message_id в state
        st = get_state(chat_id)
        if st["db_ok"]:
            set_state(chat_id, step=st["step"], ui_message_id=message_id, payload=st["payload"])

        if data == CB_MENU:
            if st["db_ok"]:
                clear_step_keep_ui(chat_id)
            edit_message(chat_id, message_id, start_text(), main_menu_inline())
            return jsonify({"ok": True})

        if data == CB_INFO:
            edit_message(chat_id, message_id, info_text(), back_inline())
            return jsonify({"ok": True})

        if data in (CB_SLEEP, CB_CNS, CB_RECOVERY, CB_PRESSURE):
            edit_message(chat_id, message_id, "⏳ Модуль скоро.", back_inline())
            return jsonify({"ok": True})

        if data in (CB_BIOTIME, CB_BIOTIME_NEW):
            start_biotime_wizard(chat_id, message_id)
            return jsonify({"ok": True})

        return jsonify({"ok": True})

    # ==== TEXT ====
    message = update.get("message") or {}
    chat_id = (message.get("chat") or {}).get("id")
    incoming_message_id = message.get("message_id")
    text = (message.get("text") or "").strip()
    username = (message.get("from") or {}).get("username")

    if not chat_id:
        return jsonify({"ok": True})

    # DEBUG
    if text == "/debug":
        st = get_state(chat_id)
        send_message(
            chat_id,
            "DEBUG:\n"
            f"db_ok: {st['db_ok']}\n"
            f"db_msg: {st['db_msg']}\n"
            f"step: {st['step']}\n"
            f"ui_message_id: {st['ui_message_id']}\n"
            f"payload_keys: {list((st['payload'] or {}).keys())}"
        )
        return jsonify({"ok": True})

    # /start /menu
    if text.startswith("/start") or text == "/menu":
        try_delete_user_message(chat_id, incoming_message_id)
        ensure_ui(chat_id)
        return jsonify({"ok": True})

    # Wizard
    st = get_state(chat_id)
    if not st["db_ok"]:
        send_message(chat_id, f"⚠️ БД недоступна: {st['db_msg']}")
        return jsonify({"ok": True})

    step = st["step"]
    payload = st["payload"] or {}
    mid = st["ui_message_id"] or ensure_ui(chat_id)

    if step:
        try_delete_user_message(chat_id, incoming_message_id)

        try:
            if step == STEP_BT_SLEEP_HOURS:
                v = parse_float(text)
                if v <= 0 or v > 14:
                    raise ValueError()
                payload["sleep_hours"] = v

            elif step == STEP_BT_LATENCY_MIN:
                v = parse_int(text)
                if v < 0 or v > 240:
                    raise ValueError()
                payload["latency_min"] = v

            elif step == STEP_BT_AWAKENINGS:
                v = parse_int(text)
                if v < 0 or v > 20:
                    raise ValueError()
                payload["awakenings"] = v

            elif step == STEP_BT_MORNING_FEEL:
                v = parse_float(text)
                if v < 0 or v > 10:
                    raise ValueError()
                payload["morning_feel"] = v

            elif step == STEP_BT_RHR:
                v = parse_int(text)
                if v < 30 or v > 140:
                    raise ValueError()
                payload["rhr"] = v

            elif step == STEP_BT_ENERGY:
                v = parse_float(text)
                if v < 0 or v > 10:
                    raise ValueError()
                payload["energy"] = v

            elif step == STEP_BT_PRESSURE:
                payload["pressure"] = parse_pressure(text)

        except Exception:
            edit_message(chat_id, mid, "⚠️ Не понял значение.\n\n" + prompt(step), back_inline())
            set_state(chat_id, step=step, ui_message_id=mid, payload=payload)
            return jsonify({"ok": True})

        nxt = next_step(step)
        if nxt:
            set_state(chat_id, step=nxt, ui_message_id=mid, payload=payload)
            edit_message(chat_id, mid, prompt(nxt), back_inline())
            return jsonify({"ok": True})

        # finalize
        biotime = compute_biotime_from_payload(payload)
        status, level, advice = classify_biotime(biotime)
        save_biotime_entry(chat_id, payload, biotime, status, level, advice)
        core_animation_async(chat_id, mid, biotime)

        clear_step_keep_ui(chat_id)
        return jsonify({"ok": True})

    # если step нет — НЕ спамим меню, а просто игнор/или держим UI
    ensure_ui(chat_id)
    return jsonify({"ok": True})

# init under gunicorn
init_db()