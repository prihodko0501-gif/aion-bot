import os
import time
import threading
import requests
from flask import Flask, request, jsonify

import psycopg2

app = Flask(__name__)

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
API_URL = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}" if TELEGRAM_TOKEN else None

DATABASE_URL = os.environ.get("DATABASE_URL")

# ====== FALLBACK MEMORY (если БД недоступна) ======
# telegram_id -> {"step": "..."}
USER_STATE_MEM = {}
# telegram_id -> {"message_id": int}
UI_MEM = {}

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


# =========================================================
# ===================== POSTGRES HELPERS ===================
# =========================================================

def db_available() -> bool:
    return bool(DATABASE_URL)


def db_conn():
    """
    Подключение на каждую операцию (на Render это нормально).
    sslmode=require — безопасно (работает и с internal URL).
    """
    return psycopg2.connect(DATABASE_URL, sslmode="require")


def init_db():
    """
    Создаем таблицы, чтобы не было:
    psycopg2.errors.UndefinedTable: relation "user_state" does not exist
    """
    if not db_available():
        print("DB: DATABASE_URL not set, using memory only")
        return

    conn = None
    try:
        conn = db_conn()
        with conn:
            with conn.cursor() as cur:
                cur.execute("""
                CREATE TABLE IF NOT EXISTS user_state (
                    telegram_id BIGINT PRIMARY KEY,
                    step TEXT,
                    updated_at TIMESTAMP DEFAULT NOW()
                );
                """)
                cur.execute("""
                CREATE TABLE IF NOT EXISTS ui_state (
                    telegram_id BIGINT PRIMARY KEY,
                    ui_message_id BIGINT,
                    updated_at TIMESTAMP DEFAULT NOW()
                );
                """)
                cur.execute("""
                CREATE TABLE IF NOT EXISTS biotime_logs (
                    id BIGSERIAL PRIMARY KEY,
                    telegram_id BIGINT NOT NULL,
                    created_at TIMESTAMP DEFAULT NOW(),
                    sleep NUMERIC,
                    stress NUMERIC,
                    recovery NUMERIC,
                    pressure_penalty NUMERIC,
                    drop_penalty NUMERIC,
                    risk_penalty NUMERIC,
                    biotime NUMERIC
                );
                """)
        print("DB init ok")
    except Exception as e:
        print("DB init error:", repr(e))
        print("DB: fallback to memory until fixed")
    finally:
        try:
            if conn:
                conn.close()
        except Exception:
            pass


def db_get_user_step(telegram_id: int):
    if not db_available():
        return USER_STATE_MEM.get(telegram_id, {}).get("step")

    conn = None
    try:
        conn = db_conn()
        with conn:
            with conn.cursor() as cur:
                cur.execute("SELECT step FROM user_state WHERE telegram_id=%s", (telegram_id,))
                row = cur.fetchone()
                return row[0] if row else None
    except Exception as e:
        print("DB get_user_step error:", repr(e))
        return USER_STATE_MEM.get(telegram_id, {}).get("step")
    finally:
        try:
            if conn:
                conn.close()
        except Exception:
            pass


def db_set_user_step(telegram_id: int, step: str):
    if not db_available():
        USER_STATE_MEM[telegram_id] = {"step": step}
        return

    conn = None
    try:
        conn = db_conn()
        with conn:
            with conn.cursor() as cur:
                cur.execute("""
                INSERT INTO user_state (telegram_id, step, updated_at)
                VALUES (%s, %s, NOW())
                ON CONFLICT (telegram_id)
                DO UPDATE SET step=EXCLUDED.step, updated_at=NOW();
                """, (telegram_id, step))
    except Exception as e:
        print("DB set_user_step error:", repr(e))
        USER_STATE_MEM[telegram_id] = {"step": step}
    finally:
        try:
            if conn:
                conn.close()
        except Exception:
            pass


def db_clear_user_step(telegram_id: int):
    if not db_available():
        USER_STATE_MEM.pop(telegram_id, None)
        return

    conn = None
    try:
        conn = db_conn()
        with conn:
            with conn.cursor() as cur:
                cur.execute("DELETE FROM user_state WHERE telegram_id=%s", (telegram_id,))
    except Exception as e:
        print("DB clear_user_step error:", repr(e))
        USER_STATE_MEM.pop(telegram_id, None)
    finally:
        try:
            if conn:
                conn.close()
        except Exception:
            pass


def db_get_ui_message_id(telegram_id: int):
    if not db_available():
        return UI_MEM.get(telegram_id, {}).get("message_id")

    conn = None
    try:
        conn = db_conn()
        with conn:
            with conn.cursor() as cur:
                cur.execute("SELECT ui_message_id FROM ui_state WHERE telegram_id=%s", (telegram_id,))
                row = cur.fetchone()
                return int(row[0]) if row and row[0] is not None else None
    except Exception as e:
        print("DB get_ui_message_id error:", repr(e))
        return UI_MEM.get(telegram_id, {}).get("message_id")
    finally:
        try:
            if conn:
                conn.close()
        except Exception:
            pass


def db_set_ui_message_id(telegram_id: int, message_id: int):
    if not db_available():
        UI_MEM[telegram_id] = {"message_id": message_id}
        return

    conn = None
    try:
        conn = db_conn()
        with conn:
            with conn.cursor() as cur:
                cur.execute("""
                INSERT INTO ui_state (telegram_id, ui_message_id, updated_at)
                VALUES (%s, %s, NOW())
                ON CONFLICT (telegram_id)
                DO UPDATE SET ui_message_id=EXCLUDED.ui_message_id, updated_at=NOW();
                """, (telegram_id, message_id))
    except Exception as e:
        print("DB set_ui_message_id error:", repr(e))
        UI_MEM[telegram_id] = {"message_id": message_id}
    finally:
        try:
            if conn:
                conn.close()
        except Exception:
            pass


def db_insert_biotime_log(
    telegram_id: int,
    sleep: float,
    stress: float,
    recovery: float,
    pressure_penalty: float,
    drop_penalty: float,
    risk_penalty: float,
    biotime: float,
):
    if not db_available():
        return

    conn = None
    try:
        conn = db_conn()
        with conn:
            with conn.cursor() as cur:
                cur.execute("""
                INSERT INTO biotime_logs
                (telegram_id, sleep, stress, recovery, pressure_penalty, drop_penalty, risk_penalty, biotime)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s)
                """, (telegram_id, sleep, stress, recovery, pressure_penalty, drop_penalty, risk_penalty, biotime))
    except Exception as e:
        print("DB insert_biotime_log error:", repr(e))
    finally:
        try:
            if conn:
                conn.close()
        except Exception:
            pass


# =========================================================
# ========================= UI MARKUP ======================
# =========================================================

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


# =========================================================
# ==================== TELEGRAM API HELPERS ================
# =========================================================

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


# =========================================================
# ========================= TEXT BLOCKS =====================
# =========================================================

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
    biotime = round((sleep * 1.2 + recovery * 1.2 - stress) - pressure_penalty - drop_penalty - risk_penalty, 1)
    return biotime, sleep, stress, recovery, pressure_penalty, drop_penalty, risk_penalty


def result_block(biotime: float):
    score = max(0.0, min(12.0, biotime))
    filled = int(round(score))
    bar = "▰" * filled + "▱" * (12 - filled)

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


# =========================================================
# ==================== LIVE UI (one message) ===============
# =========================================================

def ensure_ui(chat_id: int):
    mid = db_get_ui_message_id(chat_id)
    if mid:
        edit_message(chat_id, mid, start_text(), main_menu_inline())
        return mid

    mid = send_message(chat_id, start_text(), main_menu_inline())
    if mid:
        db_set_ui_message_id(chat_id, mid)
    return mid


# =========================================================
# ============ STREAM-LIKE ANIMATION (THREAD) ==============
# =========================================================

def core_animation_async(chat_id: int, mid: int, biotime: float):
    """
    Анимация в отдельном потоке:
    webhook отвечает сразу, а сообщение редактируется "в реальном времени".
    """
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


# =========================================================
# ============================ ROUTES ======================
# =========================================================

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

        # запоминаем главное сообщение интерфейса
        db_set_ui_message_id(chat_id, message_id)

        if data == CB_MENU:
            db_clear_user_step(chat_id)
            edit_message(chat_id, message_id, start_text(), main_menu_inline())
            return jsonify({"ok": True})

        if data == CB_INFO:
            edit_message(chat_id, message_id, info_text(), back_inline())
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

        # BioTime: сразу ввод
        if data == CB_BIOTIME:
            db_set_user_step(chat_id, "biotime_input")
            edit_message(chat_id, message_id, biotime_prompt_text(), back_inline())
            return jsonify({"ok": True})

        # Новый расчёт -> снова на ввод
        if data == CB_BIOTIME_NEW:
            db_set_user_step(chat_id, "biotime_input")
            edit_message(chat_id, message_id, biotime_prompt_text(), back_inline())
            return jsonify({"ok": True})

        return jsonify({"ok": True})

    # ====== обычные сообщения ======
    message = update.get("message") or {}
    chat_id = (message.get("chat") or {}).get("id")
    text = (message.get("text") or "").strip()

    if not chat_id:
        return jsonify({"ok": True})

    # /start или /menu — панель убрать полностью + показать один живой интерфейс
    if text in ("/start", "/menu"):
        db_clear_user_step(chat_id)
        hide_bottom_panel_silently(chat_id)
        ensure_ui(chat_id)
        return jsonify({"ok": True})

    # ввод для BioTime
    if db_get_user_step(chat_id) == "biotime_input":
        parts = text.split()
        mid = db_get_ui_message_id(chat_id) or ensure_ui(chat_id)

        if len(parts) != 6:
            if mid:
                edit_message(chat_id, mid, "⚠️ Нужно ровно 6 чисел.\n\nПример:\n7 6 8 0 0 1", back_inline())
            return jsonify({"ok": True})

        try:
            biotime, sleep, stress, recovery, pressure_penalty, drop_penalty, risk_penalty = calc_biotime(parts)
        except Exception:
            if mid:
                edit_message(chat_id, mid, "⚠️ Ошибка формата.\n\nПример:\n7 6 8 0 0 1", back_inline())
            return jsonify({"ok": True})

        # сохранить в БД лог расчёта
        db_insert_biotime_log(
            telegram_id=chat_id,
            sleep=sleep,
            stress=stress,
            recovery=recovery,
            pressure_penalty=pressure_penalty,
            drop_penalty=drop_penalty,
            risk_penalty=risk_penalty,
            biotime=biotime,
        )

        # анимация
        if mid:
            core_animation_async(chat_id, mid, biotime)

        db_clear_user_step(chat_id)
        return jsonify({"ok": True})

    # любой другой текст — возвращаем интерфейс
    ensure_ui(chat_id)
    return jsonify({"ok": True})


# =========================================================
# ============================ START =======================
# =========================================================

# создаём таблицы при старте
init_db()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", "8080"))
    app.run(host="0.0.0.0", port=port)
