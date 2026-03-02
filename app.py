import os
import requests
import time
from flask import Flask, request, jsonify

app = Flask(__name__)

TOKEN = os.getenv("TELEGRAM_TOKEN")
API = f"https://api.telegram.org/bot{TOKEN}"

USER_STATE = {}
UI = {}

# ===== INLINE =====

def main_menu():
    return {
        "inline_keyboard": [
            [{"text": "🧬 IonCore", "callback_data": "core"}],
            [{"text": "ℹ️ System Info", "callback_data": "info"}],
        ]
    }

def back_button():
    return {
        "inline_keyboard": [
            [{"text": "⬅️ Главное меню", "callback_data": "menu"}]
        ]
    }

# ===== TELEGRAM =====

def tg(method, payload):
    try:
        requests.post(f"{API}/{method}", json=payload, timeout=10)
    except:
        pass

def edit(chat_id, message_id, text, markup=None):
    payload = {
        "chat_id": chat_id,
        "message_id": message_id,
        "text": text
    }
    if markup:
        payload["reply_markup"] = markup
    tg("editMessageText", payload)

def send(chat_id, text, markup=None):
    payload = {"chat_id": chat_id, "text": text}
    if markup:
        payload["reply_markup"] = markup
    r = requests.post(f"{API}/sendMessage", json=payload)
    if r.status_code == 200:
        return r.json()["result"]["message_id"]
    return None

def answer(callback_id):
    tg("answerCallbackQuery", {"callback_query_id": callback_id})

def remove_keyboard(chat_id):
    tg("sendMessage", {
        "chat_id": chat_id,
        "text": " ",
        "reply_markup": {"remove_keyboard": True}
    })

# ===== UI TEXT =====

def start_text():
    return (
        "🧬 AION IONCORE\n\n"
        "Премиальная система анализа\n"
        "биологического ресурса.\n\n"
        "Выберите режим:"
    )

def info_text():
    return (
        "ℹ️ IONCORE SYSTEM\n\n"
        "IonCore — адаптационный\n"
        "интеграл восстановления.\n\n"
        "Модуль анализирует:\n"
        "• Сон\n"
        "• Стресс\n"
        "• Восстановление\n"
        "• Давление\n"
        "• Риск 3d"
    )

# ===== ANIMATION =====

def core_animation(chat_id, message_id):
    steps = [
        "🧬 IONCORE\n\nИнициализация ядра...",
        "🧠 Сканирование нейрорегуляции...\n▰▱▱▱▱",
        "🫀 Анализ сосудистой нагрузки...\n▰▰▰▱▱",
        "🔥 Расчёт адаптационного интеграла...\n▰▰▰▰▰"
    ]
    for s in steps:
        edit(chat_id, message_id, s)
        time.sleep(0.7)

# ===== RESULT BLOCK =====

def result_block(score):
    bar = int(score)
    visual = "▰" * bar + "▱" * (12 - bar)

    if score < 4:
        status = "🔴 ALERT"
        advice = "Нарушен адаптационный баланс."
    elif score < 8:
        status = "🟠 CAUTION"
        advice = "Снизить объём нагрузки."
    else:
        status = "🟢 STABLE"
        advice = "Организм стабилен."

    return (
        "━━━━━━━━━━━━━━━━━━\n"
        "🧬 IONCORE RESULT\n\n"
        f"Iндекс: {score} / 12\n"
        f"{visual}\n\n"
        f"Статус: {status}\n\n"
        f"{advice}\n"
        "━━━━━━━━━━━━━━━━━━"
    )

# ===== ROUTE =====

@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.get_json()

    # CALLBACK
    if "callback_query" in data:
        cq = data["callback_query"]
        chat_id = cq["message"]["chat"]["id"]
        message_id = cq["message"]["message_id"]
        callback_id = cq["id"]
        action = cq["data"]

        answer(callback_id)

        UI[chat_id] = message_id

        if action == "menu":
            edit(chat_id, message_id, start_text(), main_menu())
            return jsonify(ok=True)

        if action == "info":
            edit(chat_id, message_id, info_text(), back_button())
            return jsonify(ok=True)

        if action == "core":
            USER_STATE[chat_id] = "await_input"
            edit(chat_id, message_id,
                 "🧬 IonCore\n\nВведите 6 чисел:\n7 6 8 0 0 1",
                 back_button())
            return jsonify(ok=True)

    # MESSAGE
    if "message" in data:
        chat_id = data["message"]["chat"]["id"]
        text = data["message"].get("text", "")

        if text == "/start":
            remove_keyboard(chat_id)
            mid = send(chat_id, start_text(), main_menu())
            UI[chat_id] = mid
            return jsonify(ok=True)

        if USER_STATE.get(chat_id) == "await_input":
            try:
                parts = list(map(float, text.split()))
                sleep, stress, recovery, p, d, r = parts
                score = round((sleep*1.2 + recovery*1.2 - stress) - p - d - r, 1)
                mid = UI.get(chat_id)
                core_animation(chat_id, mid)
                edit(chat_id, mid, result_block(score), back_button())
            except:
                pass
            USER_STATE.pop(chat_id, None)

    return jsonify(ok=True)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)