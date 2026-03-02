import os
import time
import threading
import requests
import secrets
from datetime import date

import psycopg2
import psycopg2.extras
from flask import Flask, request, jsonify

app = Flask(__name__)

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
API_URL = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}" if TELEGRAM_TOKEN else None
DATABASE_URL = os.environ.get("DATABASE_URL")  # Render Postgres

# ====== ТЕКСТЫ КНОПОК ======
BTN_BIOTIME = "🧬 BioTime"
BTN_SLEEP = "💤 Sleep"
BTN_CNS = "🧠 CNS"
BTN_RECOVERY = "🔥 Recovery"
BTN_PRESSURE = "🫀 Pressure"
BTN_INFO = "ℹ️ Info"

# ====== CALLBACK DATA ======
CB_BIOTIME = "biotime"
CB_SLEEP = "sleep"
CB_CNS = "cns"
CB_RECOVERY = "recovery"
CB_PRESSURE = "pressure"
CB_INFO = "info"
CB_MENU = "menu"
CB_BIOTIME_NEW = "biotime_new"


# ========= DB HELPERS =========

def db_enabled() -> bool:
    return bool(DATABASE_URL)

def db_conn():
    # Render Postgres обычно требует SSL
    return psycopg2.connect(DATABASE_URL, sslmode="require")

def db_exec(query, params=None, fetchone=False, fetchall=False):
    if not db_enabled():
        return None
    with db_conn() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(query, params or ())
            if fetchone:
                return cur.fetchone()
            if fetchall:
                return cur.fetchall()
            return None

def init_db():
    """
    ВАЖНО: вызываем при импорте модуля (Render/Gunicorn),
    иначе таблицы не создаются и будет ошибка "relation does not exist".
    """
    if not db_enabled():
        return

    db_exec("""
    CREATE TABLE IF NOT EXISTS users (
        id SERIAL PRIMARY KEY,
        telegram_id BIGINT UNIQUE NOT NULL,
        username TEXT,
        ref_code TEXT UNIQUE NOT NULL,
        referred_by TEXT,
        created_at TIMESTAMP NOT NULL DEFAULT NOW()
    );
    """)

    db_exec("""
    CREATE TABLE IF NOT EXISTS user_state (
        telegram_id BIGINT PRIMARY KEY,
        step TEXT,
        ui_message_id BIGINT,
        updated_at TIMESTAMP NOT NULL DEFAULT NOW()
    );
    """)

    db_exec("""
    CREATE TABLE IF NOT EXISTS biotime_entries (
        id SERIAL PRIMARY KEY,
        telegram_id BIGINT NOT NULL,
        entry_date DATE NOT NULL,
        sleep INT NOT NULL,
        stress INT NOT NULL,
        recovery INT NOT NULL,
        pressure_penalty INT NOT NULL,
        drop_penalty INT NOT NULL,
        risk_penalty INT NOT NULL,
        biotime_value NUMERIC NOT NULL,
        status TEXT,
        level TEXT,
        recommendation TEXT,
        created_at TIMESTAMP NOT NULL DEFAULT NOW()
    );
    """)

# ✅ КЛЮЧЕВОЕ ИЗМЕНЕНИЕ: создаём таблицы сразу на Render
init_db()


def parse_start_payload(text: str):
    # /start ref_ab12cd34
    parts = (text or "").strip().split()
    if len(parts) >= 2 and parts[1].startswith("ref_"):
        return parts[1].replace("ref_", "", 1)
    return None

def get_or_create_user(telegram_id: int, username, referred_by):
    if not db_enabled():
        return None

    u = db_exec("SELECT * FROM users WHERE telegram_id=%s", (telegram_id,), fetchone=True)
    if u:
        return u

    ref_code = secrets.token_hex(4)
    db_exec(
        "INSERT INTO users (telegram_id, username, ref_code, referred_by) VALUES (%s,%s,%s,%s)",
        (telegram_id, username, ref_code, referred_by)
    )
    return db_exec("SELECT * FROM users WHERE telegram_id=%s", (telegram_id,), fetchone=True)

def set_state(telegram_id: int, step=None, ui_message_id=None):
    if not db_enabled():
        return
    db_exec("""
        INSERT INTO user_state (telegram_id, step, ui_message_id, updated_at)
        VALUES (%s,%s,%s,NOW())
        ON CONFLICT (telegram_id) DO UPDATE
        SET step=EXCLUDED.step,
            ui_message_id=COALESCE(EXCLUDED.ui_message_id, user_state.ui_message_id),
            updated_at=NOW();
    """, (telegram_id, step, ui_message_id))

def get_state(telegram_id: int):
    if not db_enabled():
        return None
    return db_exec("SELECT * FROM user_state WHERE telegram_id=%s", (telegram_id,), fetchone=True)


# ========= UI MARKUP =========

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


# ========= TELEGRAM API HELPERS =========

def api_post(method: str, payload: dict, timeout: int = 10):
    if not API_URL:
        return None
    try:
        r = requests.post(f"{API_URL}/{method}", json=payload, timeout=timeout)
        if r.status_code == 200:
            return r.json()
    except Exception:
        pass
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

def answer_callback(callback_query_id: str):
    api_post("answerCallbackQuery", {"callback_query_id": callback_query_id})

def hide_bottom_panel_silently(chat_id: int):
    """
    Убираем ReplyKeyboard (серую нижнюю панель) и удаляем тех. сообщение.
    """
    msg_id = send_message(chat_id, "…", reply_markup={"remove_keyboard": True})
    if msg_id:
        delete_message(chat_id, msg_id)


# ========= TEXT BLOCKS =========

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

def biotime_prompt_text():
    return (
        "🧬 BioTime — ввод данных\n\n"
        "Введите 6 чисел через пробел:\n"
        "Sleep Stress Recovery PressurePenalty DropPenalty RiskPenalty\n\n"
        "Пример:\n"
        "7 6 8 0 0 1"
    )

def calc_biotime(parts):
    sleep = float(parts[0])
    stress = float(parts[1])
    recovery = float(parts[2])
    pressure_penalty = float(parts[3])
    drop_penalty = float(parts[4])
    risk_penalty = float(parts[5])
    return round((sleep * 1.2 + recovery * 1.2 - stress) - pressure_penalty - drop_penalty - risk_penalty, 1)

def classify_biotime(biotime: float):
    if biotime < 4:
        level = "🔴 Высокая"
        advice = "Разгрузка / восстановление"
        status = "ALERT MODE"
    elif biotime < 8:
        level = "🟠 Средняя"
        advice = "Снизить объём"
        status = "CAUTION"
    elif biotime <= 11:
        level = "🟡 Норма"
        advice = "Без форсирования"
        status = "NORMAL"
    else:
        level = "🟢 Оптимум"
        advice = "Работай по плану"
        status = "OPTIMAL"
    return status, level, advice

def result_block(biotime: float):
    score = max(0.0, min(12.0, biotime))
    filled = int(round(score))
    bar = "▰" * filled + "▱" * (12 - filled)

    status, level, advice = classify_biotime(biotime)

    return (
        "━━━━━━━━━━━━━━━━━━\n"
        "🧬 BioTime\n\n"
        f"Индекс: {biotime} / 12\n"
        f"{bar}\n\n"
        f"Статус: {status}\n"
        f"Уровень: {level}\n\n"
        f"Рекомендация: {advice}\n"
        "━━━━━━━━━━━━━━━━━━"
    )


# ========= LIVE UI (one message) =========

def ensure_ui(chat_id: int):
    st = get_state(chat_id) if db_enabled() else None
    mid = st.get("ui_message_id") if st else None

    if mid:
        edit_message(chat_id, mid, start_text(), main_menu_inline())
        return mid

    mid = send_message(chat_id, start_text(), main_menu_inline())
    if mid and db_enabled():
        set_state(chat_id, step=None, ui_message_id=mid)
    return mid


# ========= STREAM-LIKE ANIMATION (THREAD) =========

def core_animation_async(chat_id: int, mid: int, biotime: float):
    def run():
        try:
            steps = [
                ("🧬 BioTime\n\nИнициализация...", biotime_result_inline()),
                ("🧠 Анализ нервной регуляции…\n▰▱▱▱▱", biotime_result_inline()),
                ("🫀 Анализ нагрузки…\n▰▰▰▱▱", biotime_result_inline()),
                ("🔥 Сбор интеграла…\n▰▰▰▰▰", biotime_result_inline()),
            ]
            for txt, mk in steps:
                edit_message(chat_id, mid, txt, mk)
                time.sleep(0.25)

            edit_message(chat_id, mid, result_block(biotime), biotime_result_inline())
        except Exception:
            pass

    threading.Thread(target=run, daemon=True).start()


# ========= ROUTES =========

@app.get("/")
def home():
    return "AION is alive 🚀", 200


@app.post("/webhook")
def webhook():
    if not TELEGRAM_TOKEN:
        return jsonify({"error": "No TELEGRAM_TOKEN"}), 500

    update = request.get_json(silent=True) or {}

    # ====== INLINE нажатия ======
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

        if db_enabled():
            set_state(chat_id, step=None, ui_message_id=message_id)

        if data == CB_MENU:
            edit_message(chat_id, message_id, start_text(), main_menu_inline())
            if db_enabled():
                set_state(chat_id, step=None, ui_message_id=message_id)
            return jsonify({"ok": True})

        if data == CB_INFO:
            edit_message(chat_id, message_id, info_text(), back_inline())
            if db_enabled():
                set_state(chat_id, step=None, ui_message_id=message_id)
            return jsonify({"ok": True})

        if data == CB_SLEEP:
            edit_message(chat_id, message_id, "💤 Sleep модуль.", back_inline())
            return jsonify({"ok": True})

        if data == CB_CNS:
            edit_message(chat_id, message_id, "🧠 CNS модуль.", back_inline())
            return jsonify({"ok": True})

        if data == CB_RECOVERY:
            edit_message(chat_id, message_id, "🔥 Recovery модуль.", back_inline())
            return jsonify({"ok": True})

        if data == CB_PRESSURE:
            edit_message(chat_id, message_id, "🫀 Pressure модуль.", back_inline())
            return jsonify({"ok": True})

        if data == CB_BIOTIME:
            edit_message(chat_id, message_id, biotime_prompt_text(), back_inline())
            if db_enabled():
                set_state(chat_id, step="biotime_input", ui_message_id=message_id)
            return jsonify({"ok": True})

        if data == CB_BIOTIME_NEW:
            edit_message(chat_id, message_id, biotime_prompt_text(), back_inline())
            if db_enabled():
                set_state(chat_id, step="biotime_input", ui_message_id=message_id)
            return jsonify({"ok": True})

        return jsonify({"ok": True})

    # ====== обычные сообщения ======
    message = update.get("message") or {}
    chat_id = (message.get("chat") or {}).get("id")
    text = (message.get("text") or "").strip()
    username = (message.get("from") or {}).get("username")

    if not chat_id:
        return jsonify({"ok": True})

    if text.startswith("/start") or text == "/menu":
        hide_bottom_panel_silently(chat_id)

        if db_enabled():
            referred_by = parse_start_payload(text) if text.startswith("/start") else None
            get_or_create_user(chat_id, username, referred_by)

        mid = ensure_ui(chat_id)
        if db_enabled():
            set_state(chat_id, step=None, ui_message_id=mid)

        return jsonify({"ok": True})

    st = get_state(chat_id) if db_enabled() else None
    if st and st.get("step") == "biotime_input":
        parts = text.split()
        mid = st.get("ui_message_id") or ensure_ui(chat_id)

        if len(parts) != 6:
            if mid:
                edit_message(chat_id, mid, "⚠️ Нужно ровно 6 чисел.\n\nПример:\n7 6 8 0 0 1", back_inline())
            return jsonify({"ok": True})

        try:
            biotime = calc_biotime(parts)
        except Exception:
            if mid:
                edit_message(chat_id, mid, "⚠️ Ошибка формата.\n\nПример:\n7 6 8 0 0 1", back_inline())
            return jsonify({"ok": True})

        # сохранить в БД
        if db_enabled():
            try:
                sleep_i, stress_i, rec_i, ppen, dpen, rpen = map(int, parts)
                status, level, advice = classify_biotime(biotime)
                db_exec("""
                    INSERT INTO biotime_entries
                    (telegram_id, entry_date, sleep, stress, recovery, pressure_penalty, drop_penalty, risk_penalty,
                     biotime_value, status, level, recommendation)
                    VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                """, (
                    chat_id, date.today(),
                    sleep_i, stress_i, rec_i, ppen, dpen, rpen,
                    biotime, status, level, advice
                ))
            except Exception:
                pass

        if mid:
            core_animation_async(chat_id, mid, biotime)

        if db_enabled():
            set_state(chat_id, step=None, ui_message_id=mid)

        return jsonify({"ok": True})

    ensure_ui(chat_id)
    return jsonify({"ok": True})


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "8080"))
    app.run(host="0.0.0.0", port=port)