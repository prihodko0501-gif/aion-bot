import os
import time
import requests
from flask import Flask, request, jsonify

app = Flask(__name__)

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
API_URL = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}" if TELEGRAM_TOKEN else None

# chat_id -> {"step": "..."}
USER_STATE = {}

# chat_id -> {"message_id": int}  (главное сообщение интерфейса)
UI = {}

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
    Скрываем ReplyKeyboard (серую панель) и сразу удаляем техническое сообщение,
    чтобы в чате ничего не осталось.
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
        "🧬 BioTime модуль\n\n"
        "Введите 6 чисел через пробел:\n"
        "Sleep Stress Recovery PressurePenalty DropPenalty RiskPenalty\n\n"
        "Пример:\n"
        "7 6 8 0 0 1"
    )


def result_block(biotime: float):
    # Визуальная шкала под 12
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


# ========= LIVE UI (one message) =========

def ensure_ui(chat_id: int):
    """
    Гарантируем, что у пользователя есть одно главное сообщение интерфейса.
    Если уже есть — редактируем его. Если нет — создаём.
    """
    if chat_id in UI and UI[chat_id].get("message_id"):
        mid = UI[chat_id]["message_id"]
        edit_message(chat_id, mid, start_text(), main_menu_inline())
        return mid

    mid = send_message(chat_id, start_text(), main_menu_inline())
    if mid:
        UI[chat_id] = {"message_id": mid}
    return mid


def set_screen(chat_id: int, text: str, reply_markup=None):
    """
    Обновить главное сообщение (если его нет — создать).
    """
    mid = UI.get(chat_id, {}).get("message_id")
    if not mid:
        mid = ensure_ui(chat_id)
    if mid:
        edit_message(chat_id, mid, text, reply_markup)
    return mid


# ========= FAST ANIMATION (safe for webhook) =========

def core_animation(chat_id: int, mid: int):
    """
    Очень короткая анимация (< ~1.2 сек), чтобы не ловить 502.
    """
    steps = [
        "🧬 BioTime\n\nИнициализация...",
        "🧠 Анализ нервной регуляции…\n▰▱▱▱▱",
        "🫀 Анализ нагрузки…\n▰▰▰▱▱",
        "🔥 Сбор интеграла…\n▰▰▰▰▰",
    ]
    for s in steps:
        edit_message(chat_id, mid, s, back_inline())
        time.sleep(0.25)  # коротко


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

        # запоминаем главное сообщение интерфейса
        UI[chat_id] = {"message_id": message_id}

        if data == CB_MENU:
            USER_STATE.pop(chat_id, None)
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

        if data == CB_BIOTIME:
            USER_STATE[chat_id] = {"step": "biotime_input"}
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
        USER_STATE.pop(chat_id, None)
        hide_bottom_panel_silently(chat_id)   # <-- серую панель убираем
        ensure_ui(chat_id)                    # <-- одно главное сообщение
        return jsonify({"ok": True})

    # ввод для BioTime
    if USER_STATE.get(chat_id, {}).get("step") == "biotime_input":
        parts = text.split()
        mid = UI.get(chat_id, {}).get("message_id") or ensure_ui(chat_id)

        if len(parts) != 6:
            # вместо спама — аккуратно обновим главное сообщение подсказкой
            if mid:
                edit_message(chat_id, mid, "⚠️ Нужно ровно 6 чисел.\n\nПример:\n7 6 8 0 0 1", back_inline())
            return jsonify({"ok": True})

        try:
            sleep = float(parts[0])
            stress = float(parts[1])
            recovery = float(parts[2])
            pressure_penalty = float(parts[3])
            drop_penalty = float(parts[4])
            risk_penalty = float(parts[5])
        except Exception:
            if mid:
                edit_message(chat_id, mid, "⚠️ Ошибка формата.\n\nПример:\n7 6 8 0 0 1", back_inline())
            return jsonify({"ok": True})

        biotime = round((sleep * 1.2 + recovery * 1.2 - stress) - pressure_penalty - drop_penalty - risk_penalty, 1)

        if mid:
            core_animation(chat_id, mid)  # мини-анимация
            edit_message(chat_id, mid, result_block(biotime), back_inline())

        USER_STATE.pop(chat_id, None)
        return jsonify({"ok": True})

    # любой другой текст — возвращаем интерфейс (без спама)
    ensure_ui(chat_id)
    return jsonify({"ok": True})


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "8080"))
    app.run(host="0.0.0.0", port=port)