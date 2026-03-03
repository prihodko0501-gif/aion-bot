import os
import time
import threading
import requests
from datetime import date
import secrets

from flask import Flask, request, jsonify

import psycopg2
import psycopg2.extras

app = Flask(__name__)

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
API_URL = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}" if TELEGRAM_TOKEN else None
DATABASE_URL = os.environ.get("DATABASE_URL")  # Render Postgres (optional)

# ====== MEMORY FALLBACK ======
MEM_STATE = {}   # chat_id -> {"step": str|None, "payload": dict}
MEM_UI = {}      # chat_id -> {"ui_message_id": int|None}

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

    db_exec("""
    CREATE TABLE IF NOT EXISTS aion_state (
        telegram_id BIGINT PRIMARY KEY,
        ui_message_id BIGINT,
        step TEXT,
        payload_json JSONB NOT NULL DEFAULT '{}'::jsonb,
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
    if db_enabled():
        row = db_exec("SELECT * FROM aion_state WHERE telegram_id=%s", (chat_id,), fetchone=True)
        if row is not None:
            # гарантируем ключи
            row.setdefault("payload_json", {})
            return row

    return {
        "telegram_id": chat_id,
        "ui_message_id": MEM_UI.get(chat_id, {}).get("ui_message_id"),
        "step": MEM_STATE.get(chat_id, {}).get("step"),
        "payload_json": MEM_STATE.get(chat_id, {}).get("payload", {}),
    }

def set_state(chat_id: int, step=None, ui_message_id=None, payload=None):
    # memory
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

    if not db_enabled():
        return

    step_db = step if step is not None else None
    payload_db = psycopg2.extras.Json(payload) if payload is not None else None

    db_exec("""
        INSERT INTO aion_state (telegram_id, ui_message_id, step, payload_json, updated_at)
        VALUES (%s,%s,%s,COALESCE(%s,'{}'::jsonb),NOW())
        ON CONFLICT (telegram_id) DO UPDATE
        SET ui_message_id=COALESCE(EXCLUDED.ui_message_id, aion_state.ui_message_id),
            step=COALESCE(EXCLUDED.step, aion_state.step),
            payload_json=COALESCE(EXCLUDED.payload_json, aion_state.payload_json),
            updated_at=NOW();
    """, (chat_id, ui_message_id, step_db, payload_db))

def clear_state(chat_id: int, keep_ui: bool = True):
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
            INSERT INTO aion_state (telegram_id, ui_message_id, step, payload_json, updated_at)
            VALUES (%s,%s,NULL,'{}'::jsonb,NOW())
            ON CONFLICT (telegram_id) DO UPDATE
            SET step=NULL,
                payload_json='{}'::jsonb,
                ui_message_id=COALESCE(EXCLUDED.ui_message_id, aion_state.ui_message_id),
                updated_at=NOW();
        """, (chat_id, ui_mid))
    else:
        db_exec("DELETE FROM aion_state WHERE telegram_id=%s", (chat_id,))

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
def api_post(method: str, payload: dict, timeout: int = 12):
    if not API_URL:
        return None
    try:
        r = requests.post(f"{API_URL}/{method}", json=payload, timeout=timeout)
        data = r.json() if r.headers.get("content-type", "").startswith("application/json") else None
        if r.status_code == 200:
            return data
        # 400 message is not modified — НЕ считаем критической ошибкой
        if data and data.get("error_code") == 400 and "message is not modified" in (data.get("description") or ""):
            return data
        print("TG ERROR", r.status_code, (r.text or "")[:300])
        return data
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

def edit_message(chat_id: int, message_id: int, text: str, reply_markup=None) -> bool:
    payload = {"chat_id": chat_id, "message_id": message_id, "text": text}
    if reply_markup is not None:
        payload["reply_markup"] = reply_markup
    data = api_post("editMessageText", payload)
    if data and data.get("ok"):
        return True
    # если "message is not modified" — считаем успешным
    if data and data.get("error_code") == 400 and "message is not modified" in (data.get("description") or ""):
        return True
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

def hide_bottom_panel_silently(chat_id: int):
    # убираем reply keyboard (если вдруг было)
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
# TEXTS / LOGIC
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
        return (
            "7) Давление утром SYS/DIA и пульс (например: 120/80 62)\n"
            "или напиши: пропусти"
        )
    return "…"

def pro_hint_text():
    return (
        "⚙️ Быстрый режим (для своих):\n"
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

    biotime = round((sleep_score * 0.6 + recovery * 0.8 - stress * 0.7) + 6.0
                    - pressure_penalty - drop_penalty - risk_penalty, 1)
    return clamp(biotime, 0.0, 12.0)

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

def calc_biotime_pro(parts):
    sleep = float(parts[0])
    stress = float(parts[1])
    recovery = float(parts[2])
    pressure_penalty = float(parts[3])
    drop_penalty = float(parts[4])
    risk_penalty = float(parts[5])
    return round((sleep * 1.2 + recovery * 1.2 - stress) - pressure_penalty - drop_penalty - risk_penalty, 1)

def safe_show_menu(chat_id: int) -> int | None:
    """
    ЖЁСТКАЯ гарантия меню.
    1) если есть ui_message_id и edit проходит — ок
    2) если edit не проходит (сообщение удалено/не найдено) — создаём новое UI и сохраняем
    """
    st = get_state(chat_id)
    mid = st.get("ui_message_id")

    if mid:
        ok = edit_message(chat_id, int(mid), start_text(), main_menu_inline())
        if ok:
            # на всякий случай обновим в стейте
            set_state(chat_id, step=None, ui_message_id=int(mid), payload=None)
            return int(mid)

    # fallback: send new UI message
    new_mid = send_message(chat_id, start_text(), main_menu_inline())
    if new_mid:
        set_state(chat_id, step=None, ui_message_id=new_mid, payload=None)
    return new_mid

def core_animation_async(chat_id: int, mid: int, biotime: float):
    def run():
        try:
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
        except Exception as e:
            print("ANIM ERROR:", repr(e))
    threading.Thread(target=run, daemon=True).start()

def next_step(step: str):
    try:
        i = WIZ_ORDER.index(step)
        return WIZ_ORDER[i + 1] if i + 1 < len(WIZ_ORDER) else None
    except Exception:
        return None

def start_biotime_wizard(chat_id: int, message_id: int):
    set_state(chat_id, step=STEP_BT_SLEEP_HOURS, ui_message_id=message_id, payload={})
    edit_message(chat_id, message_id, prompt(STEP_BT_SLEEP_HOURS), back_inline())

# =========================
# ROUTES
# =========================
@app.get("/")
def home():
    return "AION is alive 🚀", 200

@app.post("/webhook")
def webhook():
    # ВАЖНО: всегда 200, чтобы Telegram не ретраил и не спамил
    try:
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

            # фиксируем ui_message_id = текущее сообщение с кнопками
            st = get_state(chat_id)
            set_state(chat_id, step=st.get("step"), ui_message_id=message_id, payload=st.get("payload_json") or {})

            if data == CB_MENU:
                clear_state(chat_id, keep_ui=True)
                edit_message(chat_id, message_id, start_text(), main_menu_inline())
                return jsonify({"ok": True}), 200

            if data == CB_INFO:
                edit_message(chat_id, message_id, info_text(), back_inline())
                return jsonify({"ok": True}), 200

            if data == CB_SLEEP:
                edit_message(chat_id, message_id, "💤 Sleep модуль (скоро).", back_inline())
                return jsonify({"ok": True}), 200

            if data == CB_CNS:
                edit_message(chat_id, message_id, "🧠 CNS модуль (скоро).", back_inline())
                return jsonify({"ok": True}), 200

            if data == CB_RECOVERY:
                edit_message(chat_id, message_id, "🔥 Recovery модуль (скоро).", back_inline())
                return jsonify({"ok": True}), 200

            if data == CB_PRESSURE:
                edit_message(chat_id, message_id, "🫀 Pressure модуль (скоро).", back_inline())
                return jsonify({"ok": True}), 200

            if data in (CB_BIOTIME, CB_BIOTIME_NEW):
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

        # /start /menu — гарантированно показать меню
        if text.startswith("/start") or text == "/menu":
            # можно удалять /start — но меню должно появляться ВСЕГДА
            try_delete_user_message(chat_id, incoming_message_id)
            hide_bottom_panel_silently(chat_id)
            clear_state(chat_id, keep_ui=True)
            safe_show_menu(chat_id)
            return jsonify({"ok": True}), 200

        # /debug — диагностика прямо в телеге
        if text == "/debug":
            try_delete_user_message(chat_id, incoming_message_id)
            st = get_state(chat_id)
            mid = st.get("ui_message_id")
            step = st.get("step")
            payload = st.get("payload_json") or {}
            db = "ON" if db_enabled() else "OFF"
            msg = (
                "🛠 DEBUG\n\n"
                f"DB: {db}\n"
                f"ui_message_id: {mid}\n"
                f"step: {step}\n"
                f"payload_keys: {list(payload.keys())}\n"
            )
            # отправим отдельным сообщением (не в UI)
            send_message(chat_id, msg)
            return jsonify({"ok": True}), 200

        # /pro fast mode
        if text.startswith("/pro"):
            try_delete_user_message(chat_id, incoming_message_id)
            parts = text.split()
            mid = get_state(chat_id).get("ui_message_id") or safe_show_menu(chat_id)
            if not mid:
                return jsonify({"ok": True}), 200

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
        payload = st.get("payload_json") or {}
        mid = st.get("ui_message_id") or safe_show_menu(chat_id)

        if step:
            # удаляем пользовательский ввод
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
                    clear_state(chat_id, keep_ui=True)
                    safe_show_menu(chat_id)
                    return jsonify({"ok": True}), 200

            except Exception:
                if mid:
                    edit_message(chat_id, mid, "⚠️ Не понял значение.\n\n" + prompt(step), back_inline())
                return jsonify({"ok": True}), 200

            nxt = next_step(step)
            if nxt:
                set_state(chat_id, step=nxt, ui_message_id=mid, payload=payload)
                if mid:
                    edit_message(chat_id, mid, prompt(nxt), back_inline())
                return jsonify({"ok": True}), 200

            # FINALIZE
            try:
                biotime = compute_biotime_from_payload(payload)
                status, level, advice = classify_biotime(biotime)
                save_biotime_entry(chat_id, payload, biotime, status, level, advice)
                if mid:
                    core_animation_async(chat_id, mid, biotime)
            except Exception as e:
                print("FINALIZE ERROR:", repr(e))
                if mid:
                    edit_message(chat_id, mid, "⚠️ Ошибка расчёта. Нажми «Новый расчёт».", biotime_result_inline())

            clear_state(chat_id, keep_ui=True)
            return jsonify({"ok": True}), 200

        # default
        safe_show_menu(chat_id)
        return jsonify({"ok": True}), 200

    except Exception as e:
        # вообще любые ошибки — всё равно 200
        print("WEBHOOK ERROR:", repr(e))
        return jsonify({"ok": True}), 200

# IMPORTANT: init_db must run under gunicorn too
init_db()