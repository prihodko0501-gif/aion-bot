import os
import requests
from flask import Flask, request, jsonify

app = Flask(__name__)

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
PORT = int(os.environ.get("PORT", 10000))

if not TELEGRAM_TOKEN:
    print("⚠ TELEGRAM_TOKEN not set")

TELEGRAM_API_URL = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}"

USER_STATE = {}

# =========================
# TELEGRAM HELPERS
# =========================

def send_message(chat_id, text, reply_markup=None):
    payload = {
        "chat_id": chat_id,
        "text": text
    }

    if reply_markup:
        payload["reply_markup"] = reply_markup

    try:
        requests.post(
            f"{TELEGRAM_API_URL}/sendMessage",
            json=payload,
            timeout=10
        )
    except Exception as e:
        print("Send message error:", e)


def answer_callback(callback_query_id):
    try:
        requests.post(
            f"{TELEGRAM_API_URL}/answerCallbackQuery",
            json={"callback_query_id": callback_query_id},
            timeout=10
        )
    except Exception:
        pass


# =========================
# INLINE MENU
# =========================

def main_menu():
    return {
        "inline_keyboard": [
            [{"text": "🧬 BioTime", "callback_data": "biotime"}],
            [
                {"text": "💤 Sleep", "callback_data": "sleep"},
                {"text": "🧠 CNS", "callback_data": "cns"},
            ],
            [
                {"text": "🔥 Recovery", "callback_data": "recovery"},
                {"text": "❤️ Pressure", "callback_data": "pressure"},
            ],
            [{"text": "ℹ️ Info", "callback_data": "info"}],
        ]
    }


# =========================
# ROUTES
# =========================

@app.get("/")
def home():
    return "AION is alive 🚀", 200


@app.post("/webhook")
def webhook():
    update = request.get_json(silent=True) or {}

    # ===== CALLBACK BUTTONS =====
    if "callback_query" in update:
        cq = update["callback_query"]
        data = cq.get("data")
        chat_id = cq["message"]["chat"]["id"]
        answer_callback(cq["id"])

        if data == "biotime":
            USER_STATE[chat_id] = "biotime"
            send_message(
                chat_id,
                "🧬 BioTime расчёт\n\n"
                "Введи 6 чисел через пробел:\n"
                "Sleep Stress Recovery PressurePenalty DropPenalty RiskPenalty\n\n"
                "Пример:\n"
                "7 6 8 0 0 1"
            )
            return jsonify(ok=True)

        if data == "sleep":
            send_message(chat_id, "💤 Sleep модуль.", reply_markup=main_menu())
            return jsonify(ok=True)

        if data == "cns":
            send_message(chat_id, "🧠 CNS модуль.", reply_markup=main_menu())
            return jsonify(ok=True)

        if data == "recovery":
            send_message(chat_id, "🔥 Recovery модуль.", reply_markup=main_menu())
            return jsonify(ok=True)

        if data == "pressure":
            send_message(chat_id, "❤️ Pressure модуль.", reply_markup=main_menu())
            return jsonify(ok=True)

        if data == "info":
            send_message(
                chat_id,
                "🧬 AION\n\n"
                "Система управления скоростью биологического износа.\n\n"
                "Выберите модуль:",
                reply_markup=main_menu()
            )
            return jsonify(ok=True)

    # ===== TEXT MESSAGES =====
    message = update.get("message")
    if not message:
        return jsonify(ok=True)

    chat_id = message["chat"]["id"]
    text = message.get("text", "").strip()

    if text == "/start":
        USER_STATE.pop(chat_id, None)
        send_message(
            chat_id,
            "AION — система управления скоростью биологического износа.\n\nВыберите модуль:",
            reply_markup=main_menu()
        )
        return jsonify(ok=True)

    # ===== BIOTIME INPUT =====
    if USER_STATE.get(chat_id) == "biotime":
        parts = text.split()

        if len(parts) != 6:
            send_message(chat_id, "Нужно 6 чисел. Пример: 7 6 8 0 0 1")
            return jsonify(ok=True)

        try:
            sleep, stress, recovery, pressure, drop, risk = map(float, parts)
        except:
            send_message(chat_id, "Ошибка формата. Введите числа.")
            return jsonify(ok=True)

        biotime = round((sleep*1.2 + recovery*1.2 - stress) - pressure - drop - risk, 1)

        if biotime < 4:
            level = "🔴 Высокая нагрузка"
            advice = "Рекомендуется разгрузка"
        elif biotime < 8:
            level = "🟠 Средняя нагрузка"
            advice = "Снизить объём"
        elif biotime <= 11:
            level = "🟡 Норма"
            advice = "Работать без форсирования"
        else:
            level = "🟢 Оптимум"
            advice = "Можно работать по плану"

        send_message(
            chat_id,
            f"🧬 BioTime = {biotime}\n\n{level}\n\nРекомендация: {advice}",
            reply_markup=main_menu()
        )

        USER_STATE.pop(chat_id, None)
        return jsonify(ok=True)

    send_message(chat_id, "Выберите модуль:", reply_markup=main_menu())
    return jsonify(ok=True)


# =========================
# RUN
# =========================

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=PORT)
            