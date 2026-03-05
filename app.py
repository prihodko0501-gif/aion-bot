import os
import io
import csv
import time
import threading
from datetime import date, datetime, timedelta

import requests
from flask import Flask, request, jsonify

import psycopg2
import psycopg2.extras

app = Flask(__name__)

# ВАЖНО: чтобы Flask не различал /webhook и /webhook/
app.url_map.strict_slashes = False

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
API_URL = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}" if TELEGRAM_TOKEN else None
DATABASE_URL = os.environ.get("DATABASE_URL")  # Render Postgres (optional)

# =========================
# КНОПКИ МЕНЮ
# =========================
BTN_NAV = "🧭 Навигация"
BTN_NEW = "🧬 Новый расчёт"
BTN_DYNAMICS = "📊 Динамика"
BTN_HISTORY = "📚 История"
BTN_PROFILE = "🧠 Профиль"
BTN_SETTINGS = "⚙️ Настройки"
BTN_INFO = "ℹ️ О системе"
BTN_ASSIST = "💬 Помощник"

# =========================
# CALLBACKS
# =========================
CB_NAV = "nav"
CB_NEW = "calc_new"
CB_DYNAMICS = "dyn"
CB_HISTORY = "hist"
CB_PROFILE = "profile"
CB_SETTINGS = "settings"
CB_INFO = "info"
CB_ASSIST = "assist"
CB_MENU = "menu"

CB_H7 = "hist_7"
CB_H14 = "hist_14"
CB_CSV = "hist_csv"

# =========================
# BioTime wizard steps
# =========================
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
# MEMORY FALLBACK
# chat_id -> {"ui_message_id": int|None, "step": str|None, "payload": dict, "mode": str|None}
# mode: None | "assist"
# =========================
MEM_STATE = {}

# =========================
# DB LAYER
# =========================
def db_enabled() -> bool:
    return bool(DATABASE_URL)


def db_conn():
    # Render Postgres обычно требует sslmode=require
    return psycopg2.connect(DATABASE_URL, sslmode="require")


def db_exec(query, params=None, fetchone=False, fetchall=False):
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
    """
    Создаёт таблицы, если их нет, и ДОБАВЛЯЕТ недостающие колонки
    в уже существующие таблицы (авто-миграция).
    Это фиксит ошибку:
    UndefinedColumn: column "mode" of relation "aion_state" does not exist
    """
    if not db_enabled():
        print("DB disabled: DATABASE_URL not set. Using memory.")
        return

    # 1) базовые таблицы (если их нет)
    db_exec(
        """
        CREATE TABLE IF NOT EXISTS aion_state (
            telegram_id BIGINT PRIMARY KEY,
            ui_message_id BIGINT,
            step TEXT,
            mode TEXT,
            payload_json JSONB NOT NULL DEFAULT '{}'::jsonb,
            updated_at TIMESTAMP NOT NULL DEFAULT NOW()
        );
        """
    )

    db_exec(
        """
        CREATE TABLE IF NOT EXISTS biotime_entries (
            id BIGSERIAL PRIMARY KEY,
            telegram_id BIGINT NOT NULL,
            entry_date DATE NOT NULL,
            payload_json JSONB NOT NULL,
            biotime_value NUMERIC NOT NULL,
            status TEXT,
            level TEXT,
            recommendation TEXT,
            protocol_training TEXT,
            protocol_sleep TEXT,
            protocol_nutrition TEXT,
            created_at TIMESTAMP NOT NULL DEFAULT NOW()
        );
        """
    )

    # 2) МИГРАЦИИ: добавляем недостающие колонки в существующих таблицах
    # aion_state
    db_exec('ALTER TABLE aion_state ADD COLUMN IF NOT EXISTS ui_message_id BIGINT;')
    db_exec('ALTER TABLE aion_state ADD COLUMN IF NOT EXISTS step TEXT;')
    db_exec('ALTER TABLE aion_state ADD COLUMN IF NOT EXISTS mode TEXT;')
    db_exec("ALTER TABLE aion_state ADD COLUMN IF NOT EXISTS payload_json JSONB NOT NULL DEFAULT '{}'::jsonb;")
    db_exec('ALTER TABLE aion_state ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP NOT NULL DEFAULT NOW();')

    # biotime_entries
    db_exec('ALTER TABLE biotime_entries ADD COLUMN IF NOT EXISTS entry_date DATE;')
    db_exec("ALTER TABLE biotime_entries ADD COLUMN IF NOT EXISTS payload_json JSONB;")
    db_exec('ALTER TABLE biotime_entries ADD COLUMN IF NOT EXISTS status TEXT;')
    db_exec('ALTER TABLE biotime_entries ADD COLUMN IF NOT EXISTS level TEXT;')
    db_exec('ALTER TABLE biotime_entries ADD COLUMN IF NOT EXISTS recommendation TEXT;')
    db_exec('ALTER TABLE biotime_entries ADD COLUMN IF NOT EXISTS protocol_training TEXT;')
    db_exec('ALTER TABLE biotime_entries ADD COLUMN IF NOT EXISTS protocol_sleep TEXT;')
    db_exec('ALTER TABLE biotime_entries ADD COLUMN IF NOT EXISTS protocol_nutrition TEXT;')
    db_exec('ALTER TABLE biotime_entries ADD COLUMN IF NOT EXISTS created_at TIMESTAMP NOT NULL DEFAULT NOW();')

    print("DB init + migrate ok")


def get_state(chat_id: int):
    if db_enabled():
        row = db_exec("SELECT * FROM aion_state WHERE telegram_id=%s", (chat_id,), fetchone=True)
        if row:
            return {
                "telegram_id": chat_id,
                "ui_message_id": row.get("ui_message_id"),
                "step": row.get("step"),
                "mode": row.get("mode"),
                "payload": row.get("payload_json") or {},
            }

    st = MEM_STATE.get(chat_id) or {}
    return {
        "telegram_id": chat_id,
        "ui_message_id": st.get("ui_message_id"),
        "step": st.get("step"),
        "mode": st.get("mode"),
        "payload": st.get("payload") or {},
    }


def set_state(chat_id: int, ui_message_id=None, step=None, mode=None, payload=None):
    if chat_id not in MEM_STATE:
        MEM_STATE[chat_id] = {"ui_message_id": None, "step": None, "mode": None, "payload": {}}

    if ui_message_id is not None:
        MEM_STATE[chat_id]["ui_message_id"] = ui_message_id
    if step is not None:
        MEM_STATE[chat_id]["step"] = step
    if mode is not None:
        MEM_STATE[chat_id]["mode"] = mode
    if payload is not None:
        MEM_STATE[chat_id]["payload"] = payload

    if not db_enabled():
        return

    db_exec(
        """
        INSERT INTO aion_state (telegram_id, ui_message_id, step, mode, payload_json, updated_at)
        VALUES (%s,%s,%s,%s,%s,NOW())
        ON CONFLICT (telegram_id) DO UPDATE
        SET ui_message_id=COALESCE(EXCLUDED.ui_message_id, aion_state.ui_message_id),
            step=COALESCE(EXCLUDED.step, aion_state.step),
            mode=COALESCE(EXCLUDED.mode, aion_state.mode),
            payload_json=COALESCE(EXCLUDED.payload_json, aion_state.payload_json),
            updated_at=NOW();
        """,
        (
            chat_id,
            ui_message_id,
            step,
            mode,
            psycopg2.extras.Json(payload) if payload is not None else None,
        ),
    )


def clear_flow(chat_id: int, keep_ui=True):
    """Сброс wizard + режима помощника"""
    st = get_state(chat_id)
    ui_mid = st.get("ui_message_id") if keep_ui else None

    MEM_STATE[chat_id] = {"ui_message_id": ui_mid, "step": None, "mode": None, "payload": {}}

    if not db_enabled():
        return

    if keep_ui:
        db_exec(
            """
            INSERT INTO aion_state (telegram_id, ui_message_id, step, mode, payload_json, updated_at)
            VALUES (%s,%s,NULL,NULL,'{}'::jsonb,NOW())
            ON CONFLICT (telegram_id) DO UPDATE
            SET ui_message_id=COALESCE(EXCLUDED.ui_message_id, aion_state.ui_message_id),
                step=NULL,
                mode=NULL,
                payload_json='{}'::jsonb,
                updated_at=NOW();
            """,
            (chat_id, ui_mid),
        )
    else:
        db_exec("DELETE FROM aion_state WHERE telegram_id=%s", (chat_id,))


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


# =========================
# TELEGRAM HELPERS
# =========================
def api_post(method: str, payload: dict, timeout: int = 20):
    if not API_URL:
        print("TG: API_URL is None (no TELEGRAM_TOKEN?)")
        return None
    try:
        r = requests.post(f"{API_URL}/{method}", json=payload, timeout=timeout)
    except Exception as e:
        print("TG EXC:", repr(e))
        return None

    try:
        data = r.json()
    except Exception:
        print("TG BAD JSON:", r.status_code, (r.text or "")[:500])
        return None

    if data.get("ok"):
        return data

    desc = (data.get("description") or "").lower()
    if "message is not modified" in desc:
        return {"ok": True}

    print("TG ERROR:", r.status_code, data)
    return data


def send_message(chat_id: int, text: str, reply_markup=None):
    payload = {"chat_id": chat_id, "text": text}
    if reply_markup is not None:
        payload["reply_markup"] = reply_markup
    data = api_post("sendMessage", payload)
    if data and data.get("ok") and data.get("result"):
        return data["result"]["message_id"]
    return None


def edit_message(chat_id: int, message_id: int, text: str, reply_markup=None) -> bool:
    payload = {"chat_id": chat_id, "message_id": message_id, "text": text}
    if reply_markup is not None:
        payload["reply_markup"] = reply_markup
    data = api_post("editMessageText", payload)

    if not data:
        return False
    if data.get("ok"):
        return True

    desc = (data.get("description") or "").lower()
    if "message is not modified" in desc:
        return True
    if "message to edit not found" in desc or "message_id_invalid" in desc or "can't be edited" in desc:
        return False
    return False


def delete_message(chat_id: int, message_id: int):
    api_post("deleteMessage", {"chat_id": chat_id, "message_id": message_id})


def try_delete_user_message(chat_id: int, message_id):
    if not message_id:
        return
    try:
        delete_message(chat_id, message_id)
    except Exception:
        pass


def answer_callback(callback_query_id: str):
    api_post("answerCallbackQuery", {"callback_query_id": callback_query_id})


def send_document_bytes(chat_id: int, filename: str, file_bytes: bytes, caption: str = ""):
    """sendDocument multipart"""
    if not TELEGRAM_TOKEN:
        return
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendDocument"
    files = {"document": (filename, file_bytes)}
    data = {"chat_id": str(chat_id)}
    if caption:
        data["caption"] = caption
    try:
        r = requests.post(url, data=data, files=files, timeout=30)
        if r.status_code != 200:
            print("TG sendDocument ERROR:", r.status_code, (r.text or "")[:500])
    except Exception as e:
        print("TG sendDocument EXC:", repr(e))


# =========================
# UI MARKUP
# =========================
def main_menu_inline():
    return {
        "inline_keyboard": [
            [{"text": BTN_NAV, "callback_data": CB_NAV}],
            [{"text": BTN_NEW, "callback_data": CB_NEW}],
            [{"text": BTN_DYNAMICS, "callback_data": CB_DYNAMICS}],
            [{"text": BTN_HISTORY, "callback_data": CB_HISTORY}],
            [{"text": BTN_PROFILE, "callback_data": CB_PROFILE}],
            [{"text": BTN_SETTINGS, "callback_data": CB_SETTINGS}],
            [{"text": BTN_INFO, "callback_data": CB_INFO}],
            [{"text": BTN_ASSIST, "callback_data": CB_ASSIST}],
        ]
    }


def back_inline():
    return {"inline_keyboard": [[{"text": "⬅️ В меню", "callback_data": CB_MENU}]]}


def history_inline():
    return {
        "inline_keyboard": [
            [{"text": "📅 Показать 7 дней", "callback_data": CB_H7}],
            [{"text": "📅 Показать 14 дней", "callback_data": CB_H14}],
            [{"text": "📤 Экспорт CSV", "callback_data": CB_CSV}],
            [{"text": "⬅️ В меню", "callback_data": CB_MENU}],
        ]
    }


def after_calc_inline():
    return {
        "inline_keyboard": [
            [{"text": "🧬 Новый расчёт", "callback_data": CB_NEW}],
            [{"text": "🧭 Навигация", "callback_data": CB_NAV}],
            [{"text": "📊 Динамика", "callback_data": CB_DYNAMICS}],
            [{"text": "📚 История", "callback_data": CB_HISTORY}],
            [{"text": "💬 Помощник", "callback_data": CB_ASSIST}],
            [{"text": "⬅️ В меню", "callback_data": CB_MENU}],
        ]
    }


# =========================
# TEXTS / LOGIC
# =========================
def start_text():
    return (
        "AION — система управления скоростью\n"
        "биологического износа на основании\n"
        "анализа твоей физиологии.\n\n"
        "Выбери действие:"
    )


def info_text():
    return (
        "ℹ️ О системе AION\n\n"
        "AION отвечает на 3 вопроса:\n"
        "1) Где ты сейчас?\n"
        "2) Куда ты движешься?\n"
        "3) Что будет, если ничего не менять?\n\n"
        "Доступно:\n"
        "🧬 Новый расчёт → BioTime + протокол дня\n"
        "🧭 Навигация → индекс 0–1000 + вектор + риск\n"
        "📊 Динамика → 30–90 дней: скорость износа\n"
        "📚 История → 7/14 дней + экспорт CSV\n"
        "💬 Помощник → вопросы, но через логику AION\n\n"
        "AION PRO: /pro 7 6 8 0 0 1"
    )


def settings_text():
    return (
        "⚙️ Настройки (MVP)\n\n"
        "Скоро:\n"
        "— язык RU/EN\n"
        "— цели (сушка/масса/выносливость)\n"
        "— уведомления\n\n"
        "Пока заглушка."
    )


def profile_text(last_row):
    if not last_row:
        return (
            "🧠 Профиль\n\n"
            "Пока нет данных.\n"
            "Сделай «🧬 Новый расчёт»."
        )

    p = last_row.get("payload_json") or {}
    rhr = p.get("rhr")
    sleep = p.get("sleep_hours")
    return (
        "🧠 Профиль (MVP)\n\n"
        "Здесь будет архитектура человека:\n"
        "— толерантность к нагрузке\n"
        "— адаптационная ёмкость\n"
        "— тип нервной системы\n\n"
        "Сейчас отображаем последние базовые маркеры:\n"
        f"• Сон (последний): {sleep}\n"
        f"• Пульс покоя (последний): {rhr}\n"
    )


def prompt(step: str):
    if step == STEP_BT_SLEEP_HOURS:
        return "🧬 Новый расчёт\n\n1) Сон (часы)?\nНапример: 7.5"
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
        return '7) Давление утром SYS/DIA и пульс (например: 120/80 62)\nили напиши: "пропусти"'
    return "…"


def pro_hint_text():
    return (
        "AION PRO\n\n"
        "Формат:\n"
        "/pro Sleep Stress Recovery PressurePenalty DropPenalty RiskPenalty\n\n"
        "Пример:\n"
        "/pro 7 6 8 0 0 1"
    )


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
    bp = parts[0] if parts else ""
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


# =========================
# BIO TIME MODEL
# =========================
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
    if biotime < 7:
        mode = "ГЛУБОКОЕ ВОССТАНОВЛЕНИЕ"
        level = "🔴 Низкое"
        status = "ALERT MODE"
        advice = "Сбавь нагрузку. Восстановление приоритет."
        p_train = "Без силовых. Прогулка 20–30 мин. Лёгкая мобильность."
        p_sleep = "Лечь раньше на 1 час. Убрать экран за 60 минут. Тёмная комната."
        p_nutri = "Вода +700 мл. Магний вечером. Лёгкая еда."
    elif biotime <= 11:
        mode = "КОНТРОЛИРУЕМАЯ НАГРУЗКА"
        level = "🟡 Норма"
        status = "NORMAL"
        advice = "Работа без форсирования. Умеренный объём."
        p_train = "Умеренная тренировка 40–60 мин. Без отказа."
        p_sleep = "Обычный режим. Экран убрать за 30–40 мин."
        p_nutri = "Вода +500 мл. Обычное питание."
    else:
        mode = "ФАЗА РОСТА"
        level = "🟢 Оптимум"
        status = "OPTIMAL"
        advice = "Можно нагружать систему. Работай по плану."
        p_train = "Интенсивная работа. Сложные задачи, но без самоубийства."
        p_sleep = "Сохранить режим. Не сдвигать отбой."
        p_nutri = "Полноценное питание. Вода +700 мл."
    return status, level, advice, mode, p_train, p_sleep, p_nutri


def result_block(biotime: float, mode: str, status: str, level: str, advice: str, p_train: str, p_sleep: str, p_nutri: str):
    filled = int(round(clamp(biotime, 0, 12)))
    bar = "▰" * filled + "▱" * (12 - filled)
    return (
        "━━━━━━━━━━━━━━━━━━\n"
        "🧬 BioTime\n\n"
        f"Индекс: {biotime} / 12\n"
        f"{bar}\n\n"
        f"Режим дня: {mode}\n"
        f"Статус: {status}\n"
        f"Зона: {level}\n\n"
        f"Что делать сегодня: {advice}\n\n"
        "Протокол тренировки:\n"
        f"• {p_train}\n\n"
        "Протокол сна:\n"
        f"• {p_sleep}\n\n"
        "Питание/вода:\n"
        f"• {p_nutri}\n"
        "━━━━━━━━━━━━━━━━━━"
    )


# =========================
# AION NAVIGATION ENGINE (0–1000)
# =========================
def avg(values):
    if not values:
        return None
    return sum(values) / len(values)


def calc_nav_metrics(rows_desc):
    if not rows_desc:
        return None

    rows_asc = list(reversed(rows_desc))
    series = []
    for r in rows_asc:
        try:
            series.append(float(r.get("biotime_value")))
        except Exception:
            pass

    if not series:
        return None

    current = series[-1]
    index_1000 = int(round(clamp(current / 12.0, 0, 1) * 1000))

    last_7 = series[-7:] if len(series) >= 7 else series
    last_30 = series[-30:] if len(series) >= 30 else series

    a7 = avg(last_7)
    a30 = avg(last_30)

    delta = (a7 - a30) if (a7 is not None and a30 is not None) else 0.0
    vector = int(round(delta * 20))

    accum_days = 0
    if len(series) >= 10:
        for k in range(1, min(len(series), 30) + 1):
            sub = series[-k:]
            sub7 = sub[-7:] if len(sub) >= 7 else sub
            sub30 = sub[-30:] if len(sub) >= 30 else sub
            s7 = avg(sub7)
            s30 = avg(sub30)
            if s7 is not None and s30 is not None and (s7 < s30):
                accum_days += 1
            else:
                break

    buffer_days = int(round(clamp((a7 - 7.0), 0, 5))) if a7 is not None else 0

    base = 50.0
    if a7 is not None:
        base += (7.5 - a7) * 8.0
    base += (-delta) * 25.0

    risk = int(round(clamp(base, 5, 95)))

    if index_1000 < 420:
        regime = "ВОССТАНОВЛЕНИЕ"
    elif index_1000 < 780:
        regime = "КОНТРОЛИРУЕМАЯ НАГРУЗКА"
    else:
        regime = "РОСТ"

    return {
        "index_1000": index_1000,
        "vector": vector,
        "accum_days": accum_days,
        "buffer_days": buffer_days,
        "risk": risk,
        "regime": regime,
        "current_biotime": round(current, 1),
    }


def nav_block(rows_desc):
    m = calc_nav_metrics(rows_desc)
    if not m:
        return (
            "🧭 Навигация\n\n"
            "Пока нет данных.\n"
            "Сделай «🧬 Новый расчёт»."
        )

    idx = m["index_1000"]
    filled = int(round(idx / 1000 * 20))
    bar = "█" * filled + "░" * (20 - filled)

    v = m["vector"]
    v_arrow = "↑" if v > 0 else ("↓" if v < 0 else "→")

    return (
        "━━━━━━━━━━━━━━━━━━\n"
        "AION 1\n\n"
        f"Индекс: {idx} / 1000\n\n"
        f"[{bar}]\n\n"
        f"BioTime (последний): {m['current_biotime']} / 12\n"
        f"Вектор: {v_arrow} {v}\n"
        f"Накопление: {m['accum_days']} дн.\n"
        f"Буфер: {m['buffer_days']} дн.\n"
        f"Риск (30 дней): {m['risk']}%\n\n"
        f"Режим: {m['regime']}\n"
        "━━━━━━━━━━━━━━━━━━"
    )


def dynamics_block(rows_desc):
    if not rows_desc:
        return (
            "📊 Динамика 30–90 дней\n\n"
            "Пока нет данных.\n"
            "Сделай «🧬 Новый расчёт»."
        )

    rows_asc = list(reversed(rows_desc))
    series = []
    for r in rows_asc:
        try:
            series.append(float(r.get("biotime_value")))
        except Exception:
            pass

    if len(series) < 5:
        return (
            "📊 Динамика 30–90 дней\n\n"
            "Мало данных для динамики.\n"
            "Сделай ещё несколько расчётов."
        )

    last = series[-1]
    last7 = series[-7:] if len(series) >= 7 else series
    last30 = series[-30:] if len(series) >= 30 else series
    a7 = avg(last7)
    a30 = avg(last30)

    delta = (a7 - a30) if (a7 is not None and a30 is not None) else 0.0
    wear_rate = round(clamp((-delta) * 30.0, 0.0, 12.0), 2)

    stability = int(round(clamp((a7 / 12.0) * 100.0, 0, 100))) if a7 is not None else 0

    return (
        "📊 Динамика 30–90 дней\n\n"
        f"Последний BioTime: {round(last,1)} / 12\n"
        f"Среднее 7 дней: {round(a7,2) if a7 is not None else '-'}\n"
        f"Среднее 30 дней: {round(a30,2) if a30 is not None else '-'}\n\n"
        f"Скорость износа: {wear_rate}\n"
        f"Устойчивость системы: {stability}%\n\n"
        "Логика:\n"
        "— если 7 дней хуже 30 дней → накапливается перегруз\n"
        "— скорость износа растёт при отрицательной динамике"
    )


# =========================
# AION PRO (фиксированная формула)
# =========================
def calc_biotime_pro(parts):
    sleep = float(parts[0])
    stress = float(parts[1])
    recovery = float(parts[2])
    pressure_penalty = float(parts[3])
    drop_penalty = float(parts[4])
    risk_penalty = float(parts[5])
    biotime = round((sleep * 1.2 + recovery * 1.2 - stress) - pressure_penalty - drop_penalty - risk_penalty, 1)
    return clamp(biotime, 0.0, 12.0)


# =========================
# SINGLE UI MESSAGE
# =========================
def ensure_ui(chat_id: int):
    st = get_state(chat_id)
    mid = st.get("ui_message_id")

    if mid:
        ok = edit_message(chat_id, mid, start_text(), main_menu_inline())
        if ok:
            return mid

    new_mid = send_message(chat_id, start_text(), main_menu_inline())
    if new_mid:
        set_state(chat_id, ui_message_id=new_mid, step=None, mode=None, payload=None)
    return new_mid


def core_animation_async(chat_id: int, mid: int, final_text: str):
    def run():
        try:
            steps = [
                ("🧬 Обработка...\n▰▱▱▱▱", after_calc_inline()),
                ("🧠 Анализ...\n▰▰▱▱▱", after_calc_inline()),
                ("🫀 Оценка...\n▰▰▰▱▱", after_calc_inline()),
                ("🔥 Сбор...\n▰▰▰▰▱", after_calc_inline()),
            ]
            for txt, mk in steps:
                edit_message(chat_id, mid, txt, mk)
                time.sleep(0.25)
            edit_message(chat_id, mid, final_text, after_calc_inline())
        except Exception as e:
            print("ANIM ERROR:", repr(e))

    threading.Thread(target=run, daemon=True).start()


def next_step(step: str):
    try:
        i = WIZ_ORDER.index(step)
        return WIZ_ORDER[i + 1] if i + 1 < len(WIZ_ORDER) else None
    except Exception:
        return None


def start_biotime_wizard(chat_id: int, ui_mid: int):
    set_state(chat_id, ui_message_id=ui_mid, step=STEP_BT_SLEEP_HOURS, mode=None, payload={})
    edit_message(chat_id, ui_mid, prompt(STEP_BT_SLEEP_HOURS), back_inline())


# =========================
# HISTORY TEXT
# =========================
def history_block(rows_desc, title: str):
    if not rows_desc:
        return (
            f"📚 История ({title})\n\n"
            "Пока нет записей.\n"
            "Сделай «🧬 Новый расчёт»."
        )

    lines = [f"📚 История ({title})\n"]
    for r in rows_desc:
        ts = r.get("created_at")
        bt = r.get("biotime_value")
        lvl = r.get("level") or "-"
        rec = r.get("recommendation") or "-"
        rec_short = str(rec)
        if len(rec_short) > 60:
            rec_short = rec_short[:57] + "..."
        lines.append(f"• {ts} — {bt}/12 — {lvl} — {rec_short}")
    return "\n".join(lines)


def build_csv_bytes(rows_desc) -> bytes:
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


# =========================
# ASSISTANT (простая логика)
# =========================
def assist_intro_text():
    return (
        "💬 Помощник AION\n\n"
        "Задавай любые вопросы.\n"
        "Я отвечаю свободно, но всегда через логику AION.\n\n"
        "Если нет данных — попрошу сделать «🧬 Новый расчёт».\n\n"
        "Напиши вопрос текстом."
    )


def assist_answer(chat_id: int, question: str, last_row, nav_rows):
    q = (question or "").strip()
    if not q:
        return "Напиши вопрос текстом."

    if not last_row:
        return (
            "Сейчас нет данных по твоему состоянию.\n"
            "Сделай «🧬 Новый расчёт», и я буду отвечать точнее."
        )

    bt = float(last_row.get("biotime_value") or 0)
    lvl = last_row.get("level") or ""
    rec = last_row.get("recommendation") or ""
    m = calc_nav_metrics(nav_rows) if nav_rows else None

    head = (
        f"Текущее состояние:\n"
        f"• BioTime: {round(bt,1)}/12\n"
        f"• Зона: {lvl}\n"
        f"• Что делать сегодня: {rec}\n"
    )
    if m:
        head += f"• Индекс AION 1: {m['index_1000']}/1000, риск 30 дней: {m['risk']}%\n"

    ql = q.lower()
    if "трен" in ql or "зал" in ql or "нагруз" in ql:
        if bt < 7:
            return head + "\nПо тренировке: сегодня лучше восстановление (без тяжёлых силовых)."
        elif bt <= 11:
            return head + "\nПо тренировке: умеренно, без отказа и без добивания."
        else:
            return head + "\nПо тренировке: можно делать интенсивнее, но держи технику и сон."

    if "сон" in ql or "спат" in ql:
        return head + "\nПо сну: сегодня приоритет — стабильный отбой + убрать экран минимум за 30–60 минут."

    if "пит" in ql or "вода" in ql:
        return head + "\nПо питанию/воде: добавь воду (500–700 мл), еда без перегруза ЖКТ вечером."

    return head + "\nОтвет: уточни цель (тренировка/сон/питание/стресс), и я дам протокол точнее."


# =========================
# ROUTES: HEALTH + DEBUG
# =========================
@app.get("/")
def home():
    return jsonify({
        "ok": True,
        "service": "AION",
        "token_set": bool(TELEGRAM_TOKEN),
        "db_set": bool(DATABASE_URL),
        "api_url_set": bool(API_URL),
    }), 200


@app.get("/debug/env")
def debug_env():
    return jsonify({
        "token_set": bool(TELEGRAM_TOKEN),
        "db_set": bool(DATABASE_URL),
        "api_url_set": bool(API_URL),
    }), 200


@app.get("/debug/db")
def debug_db():
    if not db_enabled():
        return jsonify({"ok": False, "error": "DATABASE_URL not set"}), 200
    row = db_exec("SELECT NOW() as now", fetchone=True)
    return jsonify({"ok": bool(row), "row": row}), 200


# =========================
# WEBHOOK (POST) + CHECK (GET)
# =========================
@app.route("/webhook", methods=["POST", "GET"])
@app.route("/webhook/", methods=["POST", "GET"])
def webhook():
    # GET нужен только для проверки в браузере
    if request.method == "GET":
        return jsonify({
            "ok": True,
            "service": "AION webhook",
            "token_set": bool(TELEGRAM_TOKEN),
            "db_set": bool(DATABASE_URL),
            "api_url_set": bool(API_URL),
        }), 200

    # всегда 200, чтобы Telegram не делал ретраи
    if not TELEGRAM_TOKEN:
        return jsonify({"ok": True, "error": "No TELEGRAM_TOKEN"}), 200

    update = request.get_json(silent=True) or {}

    # =========================
    # CALLBACKS
    # =========================
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
            return jsonify({"ok": True}), 200

        # фиксируем UI message id
        set_state(chat_id, ui_message_id=message_id, step=None, mode=None, payload=None)

        if data == CB_MENU:
            clear_flow(chat_id, keep_ui=True)
            edit_message(chat_id, message_id, start_text(), main_menu_inline())
            return jsonify({"ok": True}), 200

        if data == CB_INFO:
            edit_message(chat_id, message_id, info_text(), back_inline())
            return jsonify({"ok": True}), 200

        if data == CB_SETTINGS:
            edit_message(chat_id, message_id, settings_text(), back_inline())
            return jsonify({"ok": True}), 200

        if data == CB_PROFILE:
            last = fetch_last_entry(chat_id) if db_enabled() else None
            edit_message(chat_id, message_id, profile_text(last), back_inline())
            return jsonify({"ok": True}), 200

        if data == CB_NEW:
            start_biotime_wizard(chat_id, message_id)
            return jsonify({"ok": True}), 200

        if data == CB_NAV:
            rows = fetch_history_limit(chat_id, limit=60) if db_enabled() else []
            edit_message(chat_id, message_id, nav_block(rows), back_inline())
            return jsonify({"ok": True}), 200

        if data == CB_DYNAMICS:
            rows = fetch_history_limit(chat_id, limit=120) if db_enabled() else []
            edit_message(chat_id, message_id, dynamics_block(rows), back_inline())
            return jsonify({"ok": True}), 200

        if data == CB_HISTORY:
            edit_message(chat_id, message_id, "📚 История\n\nВыбери период или экспорт:", history_inline())
            return jsonify({"ok": True}), 200

        if data == CB_H7:
            rows = fetch_history(chat_id, days=7) if db_enabled() else []
            edit_message(chat_id, message_id, history_block(rows, "7 дней"), history_inline())
            return jsonify({"ok": True}), 200

        if data == CB_H14:
            rows = fetch_history(chat_id, days=14) if db_enabled() else []
            edit_message(chat_id, message_id, history_block(rows, "14 дней"), history_inline())
            return jsonify({"ok": True}), 200

        if data == CB_CSV:
            if not db_enabled():
                edit_message(chat_id, message_id, "CSV доступен только при подключённой базе данных (DATABASE_URL).", back_inline())
                return jsonify({"ok": True}), 200
            rows = fetch_history_limit(chat_id, limit=500)
            b = build_csv_bytes(rows)
            send_document_bytes(chat_id, "aion_history.csv", b, caption="📤 Экспорт AION (CSV)")
            edit_message(chat_id, message_id, "Готово. CSV отправлен в чат.", history_inline())
            return jsonify({"ok": True}), 200

        if data == CB_ASSIST:
            st = get_state(chat_id)
            mid = st.get("ui_message_id") or ensure_ui(chat_id)
            set_state(chat_id, ui_message_id=mid, step=None, mode="assist", payload={})
            edit_message(chat_id, message_id, assist_intro_text(), back_inline())
            return jsonify({"ok": True}), 200

        return jsonify({"ok": True}), 200

    # =========================
    # TEXT
    # =========================
    message = update.get("message") or {}
    chat_id = (message.get("chat") or {}).get("id")
    incoming_message_id = message.get("message_id")
    text = (message.get("text") or "").strip()

    if not chat_id:
        return jsonify({"ok": True}), 200

    # /start /menu — НЕ удаляем сообщение пользователя
    if text.startswith("/start") or text == "/menu" or text.lower() in ("start", "старт"):
        clear_flow(chat_id, keep_ui=True)
        ensure_ui(chat_id)
        return jsonify({"ok": True}), 200

    # /pro — AION PRO быстрый режим
    if text.startswith("/pro"):
        try_delete_user_message(chat_id, incoming_message_id)

        parts = text.split()
        mid = get_state(chat_id).get("ui_message_id") or ensure_ui(chat_id)

        if len(parts) != 7:
            edit_message(chat_id, mid, "⚠️ Неверный формат.\n\n" + pro_hint_text(), back_inline())
            return jsonify({"ok": True}), 200

        try:
            biotime = calc_biotime_pro(parts[1:])
        except Exception:
            edit_message(chat_id, mid, "⚠️ Ошибка формата.\n\n" + pro_hint_text(), back_inline())
            return jsonify({"ok": True}), 200

        status, level, advice, mode, p_train, p_sleep, p_nutri = classify_biotime(biotime)
        final_text = result_block(biotime, mode, status, level, advice, p_train, p_sleep, p_nutri)

        save_biotime_entry(chat_id, {"pro": parts[1:]}, biotime, status, level, advice, p_train, p_sleep, p_nutri)

        core_animation_async(chat_id, mid, final_text)
        clear_flow(chat_id, keep_ui=True)
        return jsonify({"ok": True}), 200

    # Текущее состояние
    st = get_state(chat_id)
    step = st.get("step")
    mode = st.get("mode")
    payload = st.get("payload") or {}
    mid = st.get("ui_message_id") or ensure_ui(chat_id)

    # =========================
    # ASSIST MODE
    # =========================
    if mode == "assist" and not step:
        last = fetch_last_entry(chat_id) if db_enabled() else None
        rows = fetch_history_limit(chat_id, limit=60) if db_enabled() else []
        ans = assist_answer(chat_id, text, last, rows)
        edit_message(chat_id, mid, f"💬 Помощник AION\n\nВопрос: {text}\n\n{ans}", back_inline())
        return jsonify({"ok": True}), 200

    # =========================
    # WIZARD INPUT
    # =========================
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

            else:
                clear_flow(chat_id, keep_ui=True)
                ensure_ui(chat_id)
                return jsonify({"ok": True}), 200

        except Exception:
            edit_message(chat_id, mid, "⚠️ Не понял значение.\n\n" + prompt(step), back_inline())
            return jsonify({"ok": True}), 200

        nxt = next_step(step)
        if nxt:
            set_state(chat_id, ui_message_id=mid, step=nxt, mode=None, payload=payload)
            edit_message(chat_id, mid, prompt(nxt), back_inline())
            return jsonify({"ok": True}), 200

        # FINALIZE
        try:
            biotime = compute_biotime_from_payload(payload)
            status, level, advice, mode_day, p_train, p_sleep, p_nutri = classify_biotime(biotime)

            final_text = result_block(biotime, mode_day, status, level, advice, p_train, p_sleep, p_nutri)

            save_biotime_entry(chat_id, payload, biotime, status, level, advice, p_train, p_sleep, p_nutri)
            core_animation_async(chat_id, mid, final_text)

        except Exception as e:
            print("FINALIZE ERROR:", repr(e))
            edit_message(chat_id, mid, "⚠️ Ошибка расчёта. Нажми «🧬 Новый расчёт».", after_calc_inline())

        clear_flow(chat_id, keep_ui=True)
        return jsonify({"ok": True}), 200

    # =========================
    # OTHER TEXT: просто держим UI живым
    # =========================
    ensure_ui(chat_id)
    return jsonify({"ok": True}), 200


# init DB under gunicorn
init_db()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", "8080"))
    app.run(host="0.0.0.0", port=port)