import os
import time
import io
import csv
import math
import threading
import statistics
from datetime import date, datetime

import requests
from flask import Flask, request, jsonify

import psycopg2
import psycopg2.extras

app = Flask(__name__)

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
API_URL = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}" if TELEGRAM_TOKEN else None
DATABASE_URL = os.environ.get("DATABASE_URL")  # Render Postgres (optional)

# ========= MENU BUTTONS =========
BTN_NAV = "🧭 Навигация"
BTN_NEW = "🧬 Новый расчёт"
BTN_HISTORY = "📚 История"
BTN_DYNAMICS = "📊 Динамика"
BTN_PROFILE = "🧠 Профиль"
BTN_SETTINGS = "⚙️ Настройки"
BTN_INFO = "ℹ️ О системе"

# ========= CALLBACKS =========
CB_NAV = "nav"
CB_NEW = "calc_new"
CB_HISTORY = "history"
CB_DYNAMICS = "dynamics"
CB_PROFILE = "profile"
CB_SETTINGS = "settings"
CB_INFO = "info"
CB_MENU = "menu"

CB_H7 = "hist_7"
CB_H14 = "hist_14"
CB_CSV = "hist_csv"

# ========= BioTime wizard steps =========
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

# ========= MEMORY FALLBACK =========
# chat_id -> {"ui_message_id": int|None, "step": str|None, "payload": dict}
MEM_STATE = {}


# =========================
# DB LAYER
# =========================
def db_enabled() -> bool:
    return bool(DATABASE_URL)


def db_conn():
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
    if not db_enabled():
        print("DB disabled: DATABASE_URL not set. Using memory.")
        return

    db_exec(
        """
        CREATE TABLE IF NOT EXISTS aion_state (
            telegram_id BIGINT PRIMARY KEY,
            ui_message_id BIGINT,
            step TEXT,
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
            created_at TIMESTAMP NOT NULL DEFAULT NOW()
        );
        """
    )
    print("DB init ok")


def get_state(chat_id: int):
    if db_enabled():
        row = db_exec("SELECT * FROM aion_state WHERE telegram_id=%s", (chat_id,), fetchone=True)
        if row:
            return {
                "telegram_id": chat_id,
                "ui_message_id": row.get("ui_message_id"),
                "step": row.get("step"),
                "payload": row.get("payload_json") or {},
            }

    st = MEM_STATE.get(chat_id) or {}
    return {
        "telegram_id": chat_id,
        "ui_message_id": st.get("ui_message_id"),
        "step": st.get("step"),
        "payload": st.get("payload") or {},
    }


def set_state(chat_id: int, ui_message_id=None, step=None, payload=None):
    if chat_id not in MEM_STATE:
        MEM_STATE[chat_id] = {"ui_message_id": None, "step": None, "payload": {}}

    if ui_message_id is not None:
        MEM_STATE[chat_id]["ui_message_id"] = ui_message_id
    if step is not None:
        MEM_STATE[chat_id]["step"] = step
    if payload is not None:
        MEM_STATE[chat_id]["payload"] = payload

    if not db_enabled():
        return

    db_exec(
        """
        INSERT INTO aion_state (telegram_id, ui_message_id, step, payload_json, updated_at)
        VALUES (%s,%s,%s,%s,NOW())
        ON CONFLICT (telegram_id) DO UPDATE
        SET ui_message_id=COALESCE(EXCLUDED.ui_message_id, aion_state.ui_message_id),
            step=COALESCE(EXCLUDED.step, aion_state.step),
            payload_json=COALESCE(EXCLUDED.payload_json, aion_state.payload_json),
            updated_at=NOW();
        """,
        (
            chat_id,
            ui_message_id,
            step,
            psycopg2.extras.Json(payload) if payload is not None else None,
        ),
    )


def clear_wizard(chat_id: int, keep_ui=True):
    st = get_state(chat_id)
    ui_mid = st.get("ui_message_id") if keep_ui else None

    MEM_STATE[chat_id] = {"ui_message_id": ui_mid, "step": None, "payload": {}}

    if not db_enabled():
        return

    if keep_ui:
        db_exec(
            """
            INSERT INTO aion_state (telegram_id, ui_message_id, step, payload_json, updated_at)
            VALUES (%s,%s,NULL,'{}'::jsonb,NOW())
            ON CONFLICT (telegram_id) DO UPDATE
            SET ui_message_id=COALESCE(EXCLUDED.ui_message_id, aion_state.ui_message_id),
                step=NULL,
                payload_json='{}'::jsonb,
                updated_at=NOW();
            """,
            (chat_id, ui_mid),
        )
    else:
        db_exec("DELETE FROM aion_state WHERE telegram_id=%s", (chat_id,))


def save_biotime_entry(chat_id: int, payload: dict, biotime: float, status: str, level: str, advice: str):
    if not db_enabled():
        return
    db_exec(
        """
        INSERT INTO biotime_entries
        (telegram_id, entry_date, payload_json, biotime_value, status, level, recommendation)
        VALUES (%s,%s,%s,%s,%s,%s,%s)
        """,
        (chat_id, date.today(), psycopg2.extras.Json(payload), biotime, status, level, advice),
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


def fetch_history(chat_id: int, limit: int = 14):
    if not db_enabled():
        return []
    rows = db_exec(
        """
        SELECT created_at, biotime_value, status, level, recommendation
        FROM biotime_entries
        WHERE telegram_id=%s
        ORDER BY created_at DESC
        LIMIT %s
        """,
        (chat_id, limit),
        fetchall=True,
    )
    return rows or []


def fetch_series(chat_id: int, limit: int = 90):
    """Возвращает список (created_at, biotime_value) по убыванию, limit штук."""
    if not db_enabled():
        return []
    rows = db_exec(
        """
        SELECT created_at, biotime_value
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
def api_post(method: str, payload: dict, timeout: int = 12):
    if not API_URL:
        return None
    try:
        r = requests.post(f"{API_URL}/{method}", json=payload, timeout=timeout)
        data = r.json() if r.content else None
        if r.status_code == 200:
            return data
        print("TG ERROR", r.status_code, data or (r.text[:500] if r.text else ""))
        return data
    except Exception as e:
        print("TG EXC", repr(e))
        return None


def api_post_multipart(method: str, data: dict, files: dict, timeout: int = 30):
    """Для sendDocument."""
    if not API_URL:
        return None
    try:
        r = requests.post(f"{API_URL}/{method}", data=data, files=files, timeout=timeout)
        return r.json() if r.content else None
    except Exception as e:
        print("TG MULTIPART EXC", repr(e))
        return None


def send_message(chat_id: int, text: str, reply_markup=None):
    payload = {"chat_id": chat_id, "text": text}
    if reply_markup is not None:
        payload["reply_markup"] = reply_markup
    data = api_post("sendMessage", payload)
    if data and data.get("ok"):
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
# UI MARKUP
# =========================
def main_menu_inline():
    return {
        "inline_keyboard": [
            [{"text": BTN_NAV, "callback_data": CB_NAV}],
            [{"text": BTN_NEW, "callback_data": CB_NEW}],
            [{"text": BTN_HISTORY, "callback_data": CB_HISTORY}],
            [{"text": BTN_DYNAMICS, "callback_data": CB_DYNAMICS}],
            [{"text": BTN_PROFILE, "callback_data": CB_PROFILE}],
            [{"text": BTN_SETTINGS, "callback_data": CB_SETTINGS}],
            [{"text": BTN_INFO, "callback_data": CB_INFO}],
        ]
    }


def back_inline():
    return {"inline_keyboard": [[{"text": "⬅️ В меню", "callback_data": CB_MENU}]]}


def after_calc_inline():
    return {
        "inline_keyboard": [
            [{"text": "🔄 Новый расчёт", "callback_data": CB_NEW}],
            [{"text": "🧭 Навигация", "callback_data": CB_NAV}],
            [{"text": "📚 История", "callback_data": CB_HISTORY}],
            [{"text": "⬅️ В меню", "callback_data": CB_MENU}],
        ]
    }


def history_inline():
    return {
        "inline_keyboard": [
            [{"text": "Показать 7 дней", "callback_data": CB_H7}],
            [{"text": "Показать 14 дней", "callback_data": CB_H14}],
            [{"text": "Экспорт CSV", "callback_data": CB_CSV}],
            [{"text": "⬅️ В меню", "callback_data": CB_MENU}],
        ]
    }


# =========================
# TEXTS / LOGIC
# =========================
def start_text():
    return (
        "AION — система управления скоростью\n"
        "биологического износа на основе анализа\n"
        "твоей физиологии.\n\n"
        "Выбери действие:"
    )


def info_text():
    return (
        "ℹ️ О системе AION\n\n"
        "AION — это биологическая навигация:\n"
        "1) Где ты сейчас?\n"
        "2) Куда ты движешься?\n"
        "3) Что будет, если ничего не менять?\n\n"
        "Модули MVP:\n"
        "🧬 Новый расчёт → BioTime\n"
        "🧭 Навигация → индекс/вектор/риск\n"
        "📚 История → записи + экспорт\n"
        "📊 Динамика → 30–90 дней\n"
        "🧠 Профиль → архитектура человека (MVP)\n"
    )


def settings_text():
    return (
        "⚙️ Настройки (MVP)\n\n"
        "Скоро:\n"
        "— язык RU/EN\n"
        "— цели (сушка/масса/выносливость)\n"
        "— уведомления\n"
    )


def profile_text():
    return (
        "🧠 Профиль (MVP)\n\n"
        "Здесь будет архитектура человека:\n"
        "— тип нервной системы\n"
        "— толерантность к нагрузке\n"
        "— адаптационная ёмкость\n\n"
        "Пока MVP: профиль заполняем позже."
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
        "⚙️ AION PRO (для своих):\n"
        "/pro Sleep Stress Recovery PressurePenalty DropPenalty RiskPenalty\n"
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

    biotime = round((sleep_score * 0.6 + recovery * 0.8 - stress * 0.7) + 6.0 - pressure_penalty - drop_penalty - risk_penalty, 1)
    return clamp(biotime, 0.0, 12.0)


def classify_biotime(biotime: float):
    if biotime < 4:
        level = "🔴 Низкая"
        advice = "Разгрузка / восстановление"
        status = "ALERT"
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
    filled = int(round(biotime))
    bar = "▰" * filled + "▱" * (12 - filled)
    status, level, advice = classify_biotime(biotime)
    return (
        "━━━━━━━━━━━━━━━━━━\n"
        "🧬 BioTime\n\n"
        f"Индекс: {biotime} / 12\n"
        f"{bar}\n\n"
        f"Статус: {status}\n"
        f"Зона: {level}\n\n"
        f"Что делать сегодня: {advice}\n"
        "━━━━━━━━━━━━━━━━━━"
    )


def calc_biotime_pro(parts):
    sleep = float(parts[0])
    stress = float(parts[1])
    recovery = float(parts[2])
    pressure_penalty = float(parts[3])
    drop_penalty = float(parts[4])
    risk_penalty = float(parts[5])
    return round((sleep * 1.2 + recovery * 1.2 - stress) - pressure_penalty - drop_penalty - risk_penalty, 1)


# =========================
# NAVIGATION / DYNAMICS ENGINE
# =========================
def _mean(xs):
    return sum(xs) / len(xs) if xs else 0.0


def _std(xs):
    if not xs or len(xs) < 2:
        return 0.0
    return float(statistics.pstdev(xs))


def _linreg_slope(xs):
    """
    xs: значения во времени (старое -> новое)
    Возвращает наклон (примерно 'скорость изменения' на шаг).
    """
    n = len(xs)
    if n < 2:
        return 0.0
    x = list(range(n))
    x_mean = (n - 1) / 2.0
    y_mean = _mean(xs)
    num = sum((x[i] - x_mean) * (xs[i] - y_mean) for i in range(n))
    den = sum((x[i] - x_mean) ** 2 for i in range(n))
    return num / den if den else 0.0


def compute_navigation(chat_id: int):
    """
    Считает:
    - AION Index (0-1000) по последнему BioTime
    - Вектор (7д vs 14д)
    - Накопление (подряд дней < 10)
    - Буфер (дней >= 10 за 7)
    - Риск 30 дней (0-100%)
    - Стабильность (12 - std14)
    """
    last = fetch_last_entry(chat_id) if db_enabled() else None
    if not last:
        return None

    last_bt = float(last.get("biotime_value") or 0.0)
    aion_index = int(round(clamp(last_bt / 12.0, 0.0, 1.0) * 1000))

    series = fetch_series(chat_id, limit=60) if db_enabled() else []
    # series: newest -> oldest; нам нужно старое -> новое
    bts_newest = [float(r["biotime_value"]) for r in series if r.get("biotime_value") is not None]
    bts = list(reversed(bts_newest))  # old -> new

    last7 = bts[-7:] if len(bts) >= 7 else bts[:]
    last14 = bts[-14:] if len(bts) >= 14 else bts[:]

    avg7 = _mean(last7) if last7 else last_bt
    avg14 = _mean(last14) if last14 else last_bt

    delta = round(avg7 - avg14, 2)
    if delta > 0.15:
        vector = "↑"
    elif delta < -0.15:
        vector = "↓"
    else:
        vector = "→"

    # накопление: подряд дней < 10 (от сегодняшнего назад)
    accumulation = 0
    for v in reversed(bts):  # newest backwards
        if v < 10:
            accumulation += 1
        else:
            break

    # буфер: дней >= 10 за 7
    buffer_days = sum(1 for v in last7 if v >= 10)

    # стабильность: 12 - std14 (std по 0..12 шкале)
    std14 = _std(last14)
    stability = round(clamp(12.0 - std14, 0.0, 12.0), 1)

    # перегруз: дней < 8 за 14
    overload_days = sum(1 for v in last14 if v < 8)

    # риск 30д: простая модель
    # - база от overload_days (0..14) -> 0..70
    # - + от нестабильности (std14) -> 0..30
    risk = (overload_days / 14.0) * 70.0 + clamp(std14 / 2.5, 0.0, 1.0) * 30.0
    risk = int(round(clamp(risk, 0.0, 100.0)))

    return {
        "created_at": last.get("created_at"),
        "biotime": round(last_bt, 1),
        "aion_index": aion_index,
        "vector": vector,
        "delta": delta,
        "accumulation": accumulation,
        "buffer_days": buffer_days,
        "stability": stability,
        "risk": risk,
    }


def nav_block(nav: dict | None):
    if not nav:
        return (
            "🧭 Навигация\n\n"
            "Пока нет данных.\n"
            "Сделай «🧬 Новый расчёт»."
        )

    idx = nav["aion_index"]
    # полоска 0-1000 -> 20 сегментов
    filled = int(round((idx / 1000.0) * 20))
    bar = "█" * filled + "░" * (20 - filled)

    return (
        "━━━━━━━━━━━━━━━━━━\n"
        "AION 1\n\n"
        f"Индекс: {idx} / 1000\n"
        f"[{bar}]\n\n"
        f"Вектор: {nav['vector']}  ({nav['delta']:+})\n"
        f"Накопление: {nav['accumulation']} дн.\n"
        f"Буфер: {nav['buffer_days']} дн.\n"
        f"Стабильность: {nav['stability']} / 12\n"
        f"Риск 30 дней: {nav['risk']}%\n"
        "━━━━━━━━━━━━━━━━━━"
    )


def dynamics_block(chat_id: int):
    if not db_enabled():
        return "📊 Динамика\n\nБаза данных отключена. Нет истории."

    series = fetch_series(chat_id, limit=90)
    if not series:
        return "📊 Динамика\n\nПока нет данных. Сделай «🧬 Новый расчёт»."

    bts_newest = [float(r["biotime_value"]) for r in series if r.get("biotime_value") is not None]
    bts = list(reversed(bts_newest))  # old -> new

    last30 = bts[-30:] if len(bts) >= 30 else bts
    last90 = bts[-90:] if len(bts) >= 90 else bts

    avg30 = round(_mean(last30), 2) if last30 else 0.0
    avg90 = round(_mean(last90), 2) if last90 else 0.0
    slope30 = _linreg_slope(last30)  # на 1 запись
    slope30 = round(slope30, 3)

    # скорость износа: если slope отрицательный -> износ растёт
    # переводим в "баллы в месяц" примерно: slope * 30
    wear_speed = round(-slope30 * 30.0, 2)  # чем больше, тем хуже
    if wear_speed < 0:
        wear_label = "улучшение"
    elif wear_speed < 0.3:
        wear_label = "стабильно"
    elif wear_speed < 0.8:
        wear_label = "умеренный износ"
    else:
        wear_label = "ускоренный износ"

    return (
        "📊 Динамика (30–90 дней)\n\n"
        f"Среднее 30д: {avg30}\n"
        f"Среднее 90д: {avg90}\n"
        f"Тренд 30д: {slope30:+} (на запись)\n"
        f"Скорость износа: {wear_speed} / мес — {wear_label}\n\n"
        "Подсказка:\n"
        "— если тренд ↓ и износ растёт → нужен сброс нагрузки\n"
        "— если тренд ↑ → система восстанавливается\n"
    )


def history_block(rows: list[dict]):
    if not rows:
        return (
            "📚 История\n\n"
            "Пока нет записей.\n"
            "Сделай «🧬 Новый расчёт»."
        )

    lines = ["📚 История (последние записи)\n"]
    for r in rows:
        ts = r.get("created_at")
        bt = r.get("biotime_value")
        lvl = r.get("level") or "-"
        rec = r.get("recommendation") or "-"
        lines.append(f"• {ts} — {bt}/12 — {lvl} — {rec}")
    return "\n".join(lines)


def export_csv(chat_id: int, limit: int = 60):
    """Готовит CSV bytes для отправки."""
    rows = fetch_history(chat_id, limit=limit) if db_enabled() else []
    output = io.StringIO()
    w = csv.writer(output)
    w.writerow(["created_at", "biotime_value", "status", "level", "recommendation"])
    for r in rows:
        w.writerow([
            str(r.get("created_at")),
            str(r.get("biotime_value")),
            str(r.get("status")),
            str(r.get("level")),
            str(r.get("recommendation")),
        ])
    return output.getvalue().encode("utf-8")


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
        set_state(chat_id, ui_message_id=new_mid, step=None, payload=None)
    return new_mid


def core_animation_async(chat_id: int, mid: int, biotime: float):
    def run():
        try:
            steps = [
                ("🧬 BioTime\n\nИнициализация...", after_calc_inline()),
                ("🧠 Анализ данных…\n▰▱▱▱▱", after_calc_inline()),
                ("🫀 Оценка нагрузки…\n▰▰▰▱▱", after_calc_inline()),
                ("🔥 Сбор интеграла…\n▰▰▰▰▰", after_calc_inline()),
            ]
            for txt, mk in steps:
                edit_message(chat_id, mid, txt, mk)
                time.sleep(0.25)
            edit_message(chat_id, mid, result_block(biotime), after_calc_inline())
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
    set_state(chat_id, ui_message_id=ui_mid, step=STEP_BT_SLEEP_HOURS, payload={})
    edit_message(chat_id, ui_mid, prompt(STEP_BT_SLEEP_HOURS), back_inline())


# =========================
# ROUTES
# =========================
@app.get("/")
def home():
    return "AION is alive 🚀", 200


@app.post("/webhook")
def webhook():
    # всегда 200, чтобы Telegram не делал ретраи
    if not TELEGRAM_TOKEN:
        return jsonify({"ok": True, "error": "No TELEGRAM_TOKEN"}), 200

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
            return jsonify({"ok": True}), 200

        # фиксируем ui_message_id (текущее сообщение интерфейса)
        set_state(chat_id, ui_message_id=message_id, step=None, payload=None)

        if data == CB_MENU:
            clear_wizard(chat_id, keep_ui=True)
            edit_message(chat_id, message_id, start_text(), main_menu_inline())
            return jsonify({"ok": True}), 200

        if data == CB_INFO:
            edit_message(chat_id, message_id, info_text(), back_inline())
            return jsonify({"ok": True}), 200

        if data == CB_SETTINGS:
            edit_message(chat_id, message_id, settings_text(), back_inline())
            return jsonify({"ok": True}), 200

        if data == CB_PROFILE:
            edit_message(chat_id, message_id, profile_text(), back_inline())
            return jsonify({"ok": True}), 200

        if data == CB_NAV:
            nav = compute_navigation(chat_id) if db_enabled() else None
            edit_message(chat_id, message_id, nav_block(nav), back_inline())
            return jsonify({"ok": True}), 200

        if data == CB_DYNAMICS:
            edit_message(chat_id, message_id, dynamics_block(chat_id), back_inline())
            return jsonify({"ok": True}), 200

        if data == CB_HISTORY:
            rows = fetch_history(chat_id, limit=14) if db_enabled() else []
            edit_message(chat_id, message_id, history_block(rows), history_inline())
            return jsonify({"ok": True}), 200

        if data == CB_H7:
            rows = fetch_history(chat_id, limit=7) if db_enabled() else []
            edit_message(chat_id, message_id, history_block(rows), history_inline())
            return jsonify({"ok": True}), 200

        if data == CB_H14:
            rows = fetch_history(chat_id, limit=14) if db_enabled() else []
            edit_message(chat_id, message_id, history_block(rows), history_inline())
            return jsonify({"ok": True}), 200

        if data == CB_CSV:
            if not db_enabled():
                edit_message(chat_id, message_id, "📄 Экспорт CSV недоступен без базы данных.", history_inline())
                return jsonify({"ok": True}), 200

            # отправляем файл в чат (не редактируем UI этим)
            content = export_csv(chat_id, limit=60)
            filename = f"aion_history_{chat_id}.csv"
            api_post_multipart(
                "sendDocument",
                data={"chat_id": str(chat_id), "caption": "📄 История AION (CSV)"},
                files={"document": (filename, content, "text/csv")},
            )
            return jsonify({"ok": True}), 200

        if data == CB_NEW:
            start_biotime_wizard(chat_id, message_id)
            return jsonify({"ok": True}), 200

        return jsonify({"ok": True}), 200

    # ==== TEXT ====
    message = update.get("message") or {}
    chat_id = (message.get("chat") or {}).get("id")
    incoming_message_id = message.get("message_id")
    text = (message.get("text") or "").strip()

    if not chat_id:
        return jsonify({"ok": True}), 200

    t_low = (text or "").strip().lower()

    # /start /menu + поддержка "старт"/"start"
    if text.startswith("/start") or text == "/menu" or t_low in ("старт", "start"):
        clear_wizard(chat_id, keep_ui=True)
        ensure_ui(chat_id)
        return jsonify({"ok": True}), 200

    # AION PRO fast mode
    if text.startswith("/pro"):
        try_delete_user_message(chat_id, incoming_message_id)

        parts = text.split()
        mid = get_state(chat_id).get("ui_message_id") or ensure_ui(chat_id)

        if len(parts) != 7:
            edit_message(chat_id, mid, "⚠️ Формат:\n/pro 7 6 8 0 0 1\n\n" + pro_hint_text(), back_inline())
            return jsonify({"ok": True}), 200

        try:
            biotime = clamp(calc_biotime_pro(parts[1:]), 0.0, 12.0)
        except Exception:
            edit_message(chat_id, mid, "⚠️ Ошибка формата.\n\n" + pro_hint_text(), back_inline())
            return jsonify({"ok": True}), 200

        core_animation_async(chat_id, mid, biotime)
        return jsonify({"ok": True}), 200

    # Wizard input
    st = get_state(chat_id)
    step = st.get("step")
    payload = st.get("payload") or {}
    mid = st.get("ui_message_id") or ensure_ui(chat_id)

    if step:
        # скрываем ввод пользователя (цифры), чтобы не засорять чат
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
                clear_wizard(chat_id, keep_ui=True)
                ensure_ui(chat_id)
                return jsonify({"ok": True}), 200

        except Exception:
            edit_message(chat_id, mid, "⚠️ Не понял значение.\n\n" + prompt(step), back_inline())
            return jsonify({"ok": True}), 200

        nxt = next_step(step)
        if nxt:
            set_state(chat_id, ui_message_id=mid, step=nxt, payload=payload)
            edit_message(chat_id, mid, prompt(nxt), back_inline())
            return jsonify({"ok": True}), 200

        # FINALIZE
        try:
            biotime = compute_biotime_from_payload(payload)
            status, level, advice = classify_biotime(biotime)
            save_biotime_entry(chat_id, payload, biotime, status, level, advice)
            core_animation_async(chat_id, mid, biotime)
        except Exception as e:
            print("FINALIZE ERROR:", repr(e))
            edit_message(chat_id, mid, "⚠️ Ошибка расчёта. Нажми «🧬 Новый расчёт».", after_calc_inline())

        clear_wizard(chat_id, keep_ui=True)
        return jsonify({"ok": True}), 200

    # любой другой текст — просто гарантируем, что UI жив
    ensure_ui(chat_id)
    return jsonify({"ok": True}), 200


# init DB under gunicorn
init_db()