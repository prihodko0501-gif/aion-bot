import os
import time
import threading
import requests
from flask import Flask, request, jsonify

app = Flask(__name__)

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
API_URL = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}" if TELEGRAM_TOKEN else None

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

# ====== MEMORY STATE (на старте без БД) ======
STATE = {}      # chat_id -> step
UI_MSG = {}     # chat_id -> message_id


# ========= TELEGRAM =========

def api_post(method: str, payload: dict, timeout: int = 10):
    if not API_URL:
        return None
    try:
        r = requests.post(f"{API_URL}/{method}", json=payload, timeout=timeout)
        return r.json() if r.content else None
    except Exception:
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
    return api_post("editMessageText", payload)

def safe_edit_or_send(chat_id: int, message_id: int | None, text: str, reply_markup=None):
    if message_id:
        res = edit_message(chat_id, message_id, text, reply_markup)
        if res and res.get("ok"):
            return message_id
    new_id = send_message(chat_id, text, reply_markup)
    if new_id:
        UI_MSG[chat_id] = new_id
    return new_id

def answer_callback(callback_query_id: str):
    api_post("answerCallbackQuery", {"callback_query_id": callback_query_id})

def delete_message(chat_id: int, message_id: int):
    api_post("deleteMessage", {"chat_id": chat_id, "message_id": message_id})

def hide_bottom_panel_silently(chat_id: int):
    msg_id = send_message(chat_id, "…", reply_markup={"remove_keyboard": True})
    if msg_id:
        delete_message(chat_id, msg_id)


# ========= UI =========

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
    p = float(parts[3])
    d = float(parts[4])
    r = float(parts[5])
    return round((sleep * 1.2 + recovery * 1.2 - stress) - p - d - r, 1)

def result_block(biotime: float):
    score = max(0.0, min(12.0, biotime))
    filled = int(round(score))
    bar = "▰" * filled + "▱" * (12 - filled)

    if biotime < 4:
        level, advice, status = "🔴 Высокая", "Разгрузка / восстановление", "ALERT MODE"
    elif biotime < 8:
        level, advice, status = "🟠 Средняя", "Снизить объём", "CAUTION"
    elif biotime <= 11:
        level, advice, status = "🟡 Норма", "Без форсирования", "NORMAL"
    else:
        level, advice, status = "🟢 Оптимум", "Работай по плану", "OPTIMAL"

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

def core_animation_async(chat_id: int, mid: int, biotime: float):
    def run():
        steps = [
            "🧬 BioTime\n\nИнициализация...",
            "🧠 Анализ нервной регуляции…\n▰▱▱▱▱",
            "🫀 Анализ нагрузки…\n▰▰▰▱▱",
            "🔥 Сбор интеграла…\n▰▰▰▰▰",
        ]
        for txt in steps:
            edit_message(chat_id, mid, txt, biotime_result_inline())
            time.sleep(0.25)
        edit_message(chat_id, mid, result_block(biotime), biotime_result_inline())

    threading.Thread(target=run, daemon=True).start()

def ensure_ui(chat_id: int):
    mid = UI_MSG.get(chat_id)
    mid = safe_edit_or_send(chat_id, mid, start_text(), main_menu_inline())
    UI_MSG[chat_id] = mid
    return mid


# ========= ROUTES =========

@app.get("/")
def home():
    return "AION is alive 🚀", 200


@app.post("/webhook")
def webhook():
    if not TELEGRAM_TOKEN:
        return jsonify({"error": "No TELEGRAM_TOKEN"}), 500

    update = request.get_json(silent=True) or {}

    # callbacks
    if "callback_query" in update:
        cq = update["callback_query"]
        answer_callback(cq.get("id", ""))

        msg = cq.get("message") or {}
        chat_id = (msg.get("chat") or {}).get("id")
        message_id = msg.get("message_id")
        data = cq.get("data")

        if not chat_id or not message_id:
            return jsonify({"ok": True})

        UI_MSG[chat_id] = message_id

        if data == CB_MENU:
            STATE.pop(chat_id, None)
            safe_edit_or_send(chat_id, message_id, start_text(), main_menu_inline())
            return jsonify({"ok": True})

        if data == CB_INFO:
            safe_edit_or_send(chat_id, message_id, info_text(), back_inline())
            return jsonify({"ok": True})

        if data == CB_SLEEP:
            safe_edit_or_send(chat_id, message_id, "💤 Sleep модуль.", back_inline())
            return jsonify({"ok": True})

        if data == CB_CNS:
            safe_edit_or_send(chat_id, message_id, "🧠 CNS модуль.", back_inline())
            return jsonify({"ok": True})

        if data == CB_RECOVERY:
            safe_edit_or_send(chat_id, message_id, "🔥 Recovery модуль.", back_inline())
            return jsonify({"ok": True})

        if data == CB_PRESSURE:
            safe_edit_or_send(chat_id, message_id, "🫀 Pressure модуль.", back_inline())
            return jsonify({"ok": True})

        if data in (CB_BIOTIME, CB_BIOTIME_NEW):
            STATE[chat_id] = "biotime_input"
            safe_edit_or_send(chat_id, message_id, biotime_prompt_text(), back_inline())
            return jsonify({"ok": True})

        return jsonify({"ok": True})

    # messages
    message = update.get("message") or {}
    chat_id = (message.get("chat") or {}).get("id")
    text = (message.get("text") or "").strip()

    if not chat_id:
        return jsonify({"ok": True})

    if text in ("/start", "/menu"):
        STATE.pop(chat_id, None)
        hide_bottom_panel_silently(chat_id)
        ensure_ui(chat_id)
        return jsonify({"ok": True})

    if STATE.get(chat_id) == "biotime_input":
        parts = text.split()
        mid = UI_MSG.get(chat_id) or ensure_ui(chat_id)

        if len(parts) != 6:
            safe_edit_or_send(chat_id, mid, "⚠️ Нужно ровно 6 чисел.\n\nПример:\n7 6 8 0 0 1", back_inline())
            return jsonify({"ok": True})

        try:
            biotime = calc_biotime(parts)
        except Exception:
            safe_edit_or_send(chat_id, mid, "⚠️ Ошибка формата.\n\nПример:\n7 6 8 0 0 1", back_inline())
            return jsonify({"ok": True})

        STATE.pop(chat_id, None)
        core_animation_async(chat_id, mid, biotime)
        return jsonify({"ok": True})

    ensure_ui(chat_id)
    return jsonify({"ok": True})