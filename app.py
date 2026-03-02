import os
import requests
from flask import Flask, request, jsonify

app = Flask(__name__)

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
TELEGRAM_API_URL = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}" if TELEGRAM_TOKEN else None

# простое состояние: когда ждём ввод 6 чисел для BioTime
USER_STATE = {}  # chat_id -> {"step": "biotime_input"}

# ====== ТЕКСТЫ КНОПОК (как на фото) ======
BTN_BIOTIME = "🧬 BioTime"
BTN_SLEEP = "💤 Sleep"
BTN_CNS = "🧠 CNS"
BTN_RECOVERY = "🔥 Recovery"
BTN_PRESSURE = "🫀 Pressure"   # если хочешь именно 🫀 как на фото
BTN_INFO = "ℹ️ Info"

# ====== CALLBACK DATA ======
CB_BIOTIME = "biotime"
CB_SLEEP = "sleep"
CB_CNS = "cns"
CB_RECOVERY = "recovery"
CB_PRESSURE = "pressure"
CB_INFO = "info"


def main_menu_inline():
    # INLINE keyboard (кнопки под сообщением, НЕ снизу в панели)
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


def send_message(chat_id: int, text: str, reply_markup=None):
    if not TELEGRAM_API_URL:
        return
    payload = {"chat_id": chat_id, "text": text}
    if reply_markup:
        payload["reply_markup"] = reply_markup
    try:
        requests.post(f"{TELEGRAM_API_URL}/sendMessage", json=payload, timeout=10)
    except Exception:
        pass


def answer_callback(callback_query_id: str, text: str = None):
    if not TELEGRAM_API_URL:
        return
    payload = {"callback_query_id": callback_query_id}
    if text:
        payload["text"] = text
        payload["show_alert"] = False
    try:
        requests.post(f"{TELEGRAM_API_URL}/answerCallbackQuery", json=payload, timeout=10)
    except Exception:
        pass


def start_text():
    # Описание как на твоём скрине (можешь править формулировку)
    return (
        "AION — система управления скоростью\n"
        "биологического износа, основанная на\n"
        "анализе твоей физиологии.\n\n"
        "Выберите модуль:"
    )


def info_text():
    # Блок описания как на фото
    return (
        "ℹ️ AION\n"
        "AION — система управления скоростью\n"
        "биологического износа.\n\n"
        "🧬 BioTime — интегральная оценка\n"
        "восстановления.\n"
        "🫀 Pressure — давление и пульс.\n"
        "💤 Sleep — сон.\n"
        "🧠 CNS — нервная система.\n"
        "🔥 Recovery — восстановление.\n\n"
        "Выбирай модуль в меню."
    )


@app.get("/")
def home():
    return "AION is alive 🚀", 200


@app.post("/webhook")
def webhook():
    if not TELEGRAM_TOKEN:
        return jsonify({"error": "No TELEGRAM_TOKEN"}), 500

    update = request.get_json(silent=True) or {}

    # ====== 1) INLINE нажатия ======
    if "callback_query" in update:
        cq = update["callback_query"]
        callback_query_id = cq.get("id")
        data = cq.get("data")
        chat_id = cq.get("message", {}).get("chat", {}).get("id")

        if callback_query_id:
            answer_callback(callback_query_id)

        if not chat_id:
            return jsonify({"ok": True})

        # BioTime
        if data == CB_BIOTIME:
            USER_STATE[chat_id] = {"step": "biotime_input"}
            send_message(
                chat_id,
                "🧬 BioTime модуль.\n\n"
                "Введите 6 чисел. Пример:\n"
                "7 6 8 0 0 1",
                # меню можно не прикреплять, но удобно оставить:
                reply_markup=main_menu_inline()
            )
            return jsonify({"ok": True})

        # Остальные модули — короткие ответы как на скрине
        if data == CB_SLEEP:
            send_message(chat_id, "💤 Sleep модуль.", reply_markup=main_menu_inline())
            return jsonify({"ok": True})

        if data == CB_CNS:
            send_message(chat_id, "🧠 CNS модуль.", reply_markup=main_menu_inline())
            return jsonify({"ok": True})

        if data == CB_RECOVERY:
            send_message(chat_id, "🔥 Recovery модуль.", reply_markup=main_menu_inline())
            return jsonify({"ok": True})

        if data == CB_PRESSURE:
            send_message(chat_id, "🫀 Pressure модуль.", reply_markup=main_menu_inline())
            return jsonify({"ok": True})

        if data == CB_INFO:
            send_message(chat_id, info_text(), reply_markup=main_menu_inline())
            return jsonify({"ok": True})

        return jsonify({"ok": True})

    # ====== 2) Обычные сообщения ======
    message = update.get("message") or {}
    chat_id = message.get("chat", {}).get("id")
    text = (message.get("text") or "").strip()

    if not chat_id:
        return jsonify({"ok": True})

    # /start или /menu — показать меню (inline)
    if text in ("/start", "/menu"):
        USER_STATE.pop(chat_id, None)
        send_message(chat_id, start_text(), reply_markup=main_menu_inline())
        return jsonify({"ok": True})

    # Если ждём ввод для BioTime
    if USER_STATE.get(chat_id, {}).get("step") == "biotime_input":
        parts = text.split()
        if len(parts) != 6:
            send_message(chat_id, "Нужно 6 чисел. Пример:\n7 6 8 0 0 1", reply_markup=main_menu_inline())
            return jsonify({"ok": True})

        try:
            sleep = float(parts[0])
            stress = float(parts[1])
            recovery = float(parts[2])
            pressure_penalty = float(parts[3])
            drop_penalty = float(parts[4])
            risk_penalty = float(parts[5])
        except Exception:
            send_message(chat_id, "Ошибка формата. Введи 6 чисел через пробел.", reply_markup=main_menu_inline())
            return jsonify({"ok": True})

        biotime = round((sleep * 1.2 + recovery * 1.2 - stress) - pressure_penalty - drop_penalty - risk_penalty, 1)

        if biotime < 4:
            level = "🔴 Высокая"
            advice = "Разгрузка / восстановление"
        elif biotime < 8:
            level = "🟠 Средняя"
            advice = "Снизить объём"
        elif biotime <= 11:
            level = "🟡 Норма"
            advice = "Без форсирования"
        else:
            level = "🟢 Оптимум"
            advice = "Работай по плану"

        send_message(
            chat_id,
            f"🧬 BioTime = {biotime}\n{level}\n\nРекомендация: {advice}",
            reply_markup=main_menu_inline()
        )
        USER_STATE.pop(chat_id, None)
        return jsonify({"ok": True})

    # Любой другой текст — просто вернём меню
    send_message(chat_id, "Выберите модуль:", reply_markup=main_menu_inline())
    return jsonify({"ok": True})


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "8080"))
    app.run(host="0.0.0.0", port=port)
        
   

