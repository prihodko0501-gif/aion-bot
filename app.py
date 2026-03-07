import os
import math
import json
from datetime import datetime, timedelta

import requests
import psycopg2
from flask import Flask, request, jsonify

# =========================
# CONFIG
# =========================
TOKEN = os.environ.get("TELEGRAM_TOKEN", "").strip()
DATABASE_URL = os.environ.get("DATABASE_URL", "").strip()

if not TOKEN:
    raise RuntimeError("TELEGRAM_TOKEN is missing")

API_URL = f"https://api.telegram.org/bot{TOKEN}"

app = Flask(__name__)
app.url_map.strict_slashes = False

# =========================
# DB
# =========================
def get_conn():
    if not DATABASE_URL:
        return None
    return psycopg2.connect(DATABASE_URL)

def init_db():
    conn = get_conn()
    if not conn:
        print("DATABASE_URL is missing, DB disabled", flush=True)
        return

    cur = conn.cursor()

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS aion_state (
            chat_id BIGINT PRIMARY KEY,
            step TEXT,
            payload_json TEXT,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
    )

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS biotime_entries (
            id SERIAL PRIMARY KEY,
            chat_id BIGINT NOT NULL,
            sleep_hours FLOAT,
            stress FLOAT,
            recovery FLOAT,
            pressure_sys INT,
            pressure_dia INT,
            pressure_pulse INT,
            biotime FLOAT,
            aion_score FLOAT,
            advice TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
    )

    conn.commit()
    cur.close()
    conn.close()

def get_state(chat_id: int) -> dict:
    conn = get_conn()
    if not conn:
        return {"step": None, "payload": {}}

    cur = conn.cursor()
    cur.execute(
        "SELECT step, payload_json FROM aion_state WHERE chat_id = %s",
        (chat_id,),
    )
    row = cur.fetchone()
    cur.close()
    conn.close()

    if not row:
        return {"step": None, "payload": {}}

    step, payload_json = row
    payload = json.loads(payload_json) if payload_json else {}
    return {"step": step, "payload": payload}

def set_state(chat_id: int, step: str | None, payload: dict):
    conn = get_conn()
    if not conn:
        return

    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO aion_state (chat_id, step, payload_json, updated_at)
        VALUES (%s, %s, %s, CURRENT_TIMESTAMP)
        ON CONFLICT (chat_id)
        DO UPDATE SET
            step = EXCLUDED.step,
            payload_json = EXCLUDED.payload_json,
            updated_at = CURRENT_TIMESTAMP
        """,
        (chat_id, step, json.dumps(payload, ensure_ascii=False)),
    )
    conn.commit()
    cur.close()
    conn.close()

def clear_state(chat_id: int):
    conn = get_conn()
    if not conn:
        return

    cur = conn.cursor()
    cur.execute("DELETE FROM aion_state WHERE chat_id = %s", (chat_id,))
    conn.commit()
    cur.close()
    conn.close()

def save_entry(chat_id: int, payload: dict, biotime: float, aion_score: float, advice: str):
    conn = get_conn()
    if not conn:
        return

    pressure = payload.get("pressure", {})

    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO biotime_entries (
            chat_id,
            sleep_hours,
            stress,
            recovery,
            pressure_sys,
            pressure_dia,
            pressure_pulse,
            biotime,
            aion_score,
            advice
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """,
        (
            chat_id,
            payload.get("sleep_hours"),
            payload.get("stress"),
            payload.get("recovery"),
            pressure.get("sys"),
            pressure.get("dia"),
            pressure.get("pulse"),
            biotime,
            aion_score,
            advice,
        ),
    )
    conn.commit()
    cur.close()
    conn.close()

def fetch_history(chat_id: int, days: int = 7, limit: int = 15):
    conn = get_conn()
    if not conn:
        return []

    cur = conn.cursor()
    cur.execute(
        """
        SELECT created_at, biotime, aion_score
        FROM biotime_entries
        WHERE chat_id = %s
          AND created_at >= NOW() - (%s || ' days')::interval
        ORDER BY created_at DESC
        LIMIT %s
        """,
        (chat_id, str(days), limit),
    )
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return rows

# =========================
# TELEGRAM API
# =========================
def tg_post(method: str, payload: dict):
    try:
        r = requests.post(f"{API_URL}/{method}", json=payload, timeout=20)
        print(f"TG {method}: {r.status_code} {r.text}", flush=True)
        return r.json()
    except Exception as e:
        print(f"TG ERROR {method}: {e}", flush=True)
        return None

def send_message(chat_id: int, text: str, reply_markup=None):
    payload = {
        "chat_id": chat_id,
        "text": text,
    }
    if reply_markup is not None:
        payload["reply_markup"] = reply_markup
    return tg_post("sendMessage", payload)

def edit_message(chat_id: int, message_id: int, text: str, reply_markup=None):
    payload = {
        "chat_id": chat_id,
        "message_id": message_id,
        "text": text,
    }
    if reply_markup is not None:
        payload["reply_markup"] = reply_markup
    return tg_post("editMessageText", payload)

def answer_callback(callback_id: str, text: str = ""):
    payload = {"callback_query_id": callback_id}
    if text:
        payload["text"] = text
    return tg_post("answerCallbackQuery", payload)

# =========================
# UI
# =========================
CB_NEW = "new_calc"
CB_HISTORY = "history"
CB_ABOUT = "about"
CB_MENU = "menu"
CB_H7 = "hist_7"
CB_H14 = "hist_14"

STEP_SLEEP = "sleep_hours"
STEP_STRESS = "stress"
STEP_RECOVERY = "recovery"
STEP_PRESSURE = "pressure"

WIZARD_ORDER = [STEP_SLEEP, STEP_STRESS, STEP_RECOVERY, STEP_PRESSURE]

def main_menu():
    return {
        "inline_keyboard": [
            [{"text": "🧬 Новый расчёт", "callback_data": CB_NEW}],
            [{"text": "📚 История", "callback_data": CB_HISTORY}],
            [{"text": "ℹ️ О системе", "callback_data": CB_ABOUT}],
        ]
    }

def back_menu():
    return {
        "inline_keyboard": [
            [{"text": "⬅️ В меню", "callback_data": CB_MENU}]
        ]
    }

def history_menu():
    return {
        "inline_keyboard": [
            [{"text": "📅 7 дней", "callback_data": CB_H7}],
            [{"text": "📅 14 дней", "callback_data": CB_H14}],
            [{"text": "⬅️ В меню", "callback_data": CB_MENU}],
        ]
    }

def start_text():
    return (
        "AION — Biological Upgrade System\n\n"
        "Этап 2: Telegram-бот считает BioTime, "
        "сохраняет результат и показывает базовые рекомендации.\n\n"
        "Выбери действие:"
    )

def prompt(step: str) -> str:
    if step == STEP_SLEEP:
        return "🧬 Новый расчёт\n\n1) Сон (часы)?\nНапример: 7.5"
    if step == STEP_STRESS:
        return "2) Стресс (0–10)?\nНапример: 4"
    if step == STEP_RECOVERY:
        return "3) Восстановление (0–10)?\nНапример: 7"
    if step == STEP_PRESSURE:
        return '4) Давление утром SYS/DIA и пульс\nНапример: 120/80 62\n\nМожно написать: "пропусти"'
    return "Ошибка шага."

def about_text():
    return (
        "ℹ️ О системе\n\n"
        "AION — система управления биологическим состоянием.\n"
        "На этом этапе бот:\n"
        "• собирает данные\n"
        "• считает BioTime\n"
        "• сохраняет результаты\n"
        "• показывает базовые рекомендации"
    )

# =========================
# PARSING
# =========================
def parse_float_value(text: str) -> float:
    text = text.replace(",", ".").strip()
    value = float(text)
    return value

def parse_pressure(text: str) -> dict:
    text = text.strip().lower()

    if text in {"пропусти", "skip", "no"}:
        return {"sys": None, "dia": None, "pulse": None}

    parts = text.split()
    if len(parts) != 2 or "/" not in parts[0]:
        raise ValueError("pressure format")

    sys_s, dia_s = parts[0].split("/")
    pulse_s = parts[1]

    return {
        "sys": int(sys_s),
        "dia": int(dia_s),
        "pulse": int(pulse_s),
    }

# =========================
# CALC
# =========================
def calc_biotime(payload: dict) -> tuple[float, float, str]:
    sleep = float(payload.get("sleep_hours", 0))
    stress = float(payload.get("stress", 0))
    recovery = float(payload.get("recovery", 0))
    pressure = payload.get("pressure", {})

    sys = pressure.get("sys")
    dia = pressure.get("dia")

    sleep_score = max(0.0, min(10.0, (sleep / 8.0) * 10.0))
    stress_penalty = max(0.0, min(10.0, stress))
    recovery_score = max(0.0, min(10.0, recovery))

    pressure_penalty = 0.0
    if sys is not None and dia is not None:
        if sys >= 140 or dia >= 90:
            pressure_penalty = 1.5
        elif sys >= 130 or dia >= 85:
            pressure_penalty = 0.8

    biotime = round(max(0.0, min(12.0, sleep_score * 0.45 + recovery_score * 0.45 - stress_penalty * 0.35 - pressure_penalty)), 1)
    aion_score = round(max(0.0, min(100.0, biotime / 12.0 * 100.0)), 1)

    if biotime >= 8.5:
        advice = "Система в хорошем состоянии. Держи стабильный режим сна и восстановления."
    elif biotime >= 6.0:
        advice = "Состояние среднее. Снизь стресс, выровняй сон и контроль нагрузки."
    else:
        advice = "Система перегружена. Приоритет: сон, восстановление, снижение стресса."

    return biotime, aion_score, advice

def result_text(biotime: float, aion_score: float, advice: str) -> str:
    return (
        "✅ Результат AION\n\n"
        f"BioTime: {biotime}\n"
        f"AION Score: {aion_score}/100\n\n"
        f"Рекомендация:\n{advice}"
    )

# =========================
# HELPERS
# =========================
def next_step(current_step: str) -> str | None:
    try:
        idx = WIZARD_ORDER.index(current_step)
        if idx + 1 < len(WIZARD_ORDER):
            return WIZARD_ORDER[idx + 1]
        return None
    except ValueError:
        return None

def show_menu(chat_id: int):
    send_message(chat_id, start_text(), main_menu())

def show_history(chat_id: int, days: int):
    rows = fetch_history(chat_id, days=days, limit=15)

    if not rows:
        send_message(chat_id, f"📚 История за {days} дней\n\nПока записей нет.", history_menu())
        return

    lines = [f"📚 История за {days} дней\n"]
    for created_at, biotime, aion_score in rows:
        lines.append(
            f"• {created_at:%d.%m %H:%M} — BioTime {round(float(biotime), 1)} | AION {round(float(aion_score), 1)}"
        )

    send_message(chat_id, "\n".join(lines), history_menu())

# =========================
# TELEGRAM LOGIC
# =========================
def handle_message(message: dict):
    chat_id = message.get("chat", {}).get("id")
    text = (message.get("text") or "").strip()

    if not chat_id:
        return

    if text.lower() in {"/start", "start", "старт"}:
        clear_state(chat_id)
        show_menu(chat_id)
        return

    state = get_state(chat_id)
    step = state.get("step")
    payload = state.get("payload", {})

    if not step:
        show_menu(chat_id)
        return

    try:
        if step == STEP_SLEEP:
            payload["sleep_hours"] = parse_float_value(text)
        elif step == STEP_STRESS:
            payload["stress"] = parse_float_value(text)
        elif step == STEP_RECOVERY:
            payload["recovery"] = parse_float_value(text)
        elif step == STEP_PRESSURE:
            payload["pressure"] = parse_pressure(text)
    except Exception:
        send_message(chat_id, f"⚠️ Неверный формат\n\n{prompt(step)}", back_menu())
        return

    nxt = next_step(step)

    if nxt:
        set_state(chat_id, nxt, payload)
        send_message(chat_id, prompt(nxt), back_menu())
        return

    biotime, aion_score, advice = calc_biotime(payload)
    save_entry(chat_id, payload, biotime, aion_score, advice)
    clear_state(chat_id)

    send_message(chat_id, result_text(biotime, aion_score, advice), back_menu())

def handle_callback(callback: dict):
    callback_id = callback.get("id")
    data = callback.get("data", "")
    msg = callback.get("message", {})
    chat_id = msg.get("chat", {}).get("id")

    if callback_id:
        answer_callback(callback_id)

    if not chat_id:
        return

    if data == CB_MENU:
        clear_state(chat_id)
        show_menu(chat_id)
        return

    if data == CB_NEW:
        clear_state(chat_id)
        set_state(chat_id, STEP_SLEEP, {})
        send_message(chat_id, prompt(STEP_SLEEP), back_menu())
        return

    if data == CB_HISTORY:
        show_history(chat_id, 7)
        return

    if data == CB_H7:
        show_history(chat_id, 7)
        return

    if data == CB_H14:
        show_history(chat_id, 14)
        return

    if data == CB_ABOUT:
        send_message(chat_id, about_text(), back_menu())
        return

    show_menu(chat_id)

# =========================
# ROUTES
# =========================
@app.get("/")
def home():
    return "AION BOT WORKING", 200

@app.post("/webhook")
def webhook():
    data = request.get_json(silent=True) or {}
    print("TELEGRAM UPDATE:", data, flush=True)

    if "callback_query" in data:
        handle_callback(data["callback_query"])
        return jsonify({"ok": True}), 200

    if "message" in data:
        handle_message(data["message"])
        return jsonify({"ok": True}), 200

    return jsonify({"ok": True}), 200

# =========================
# RUN
# =========================
init_db()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", "10000"))
    print(f"PORT={port}", flush=True)
    app.run(host="0.0.0.0", port=port)