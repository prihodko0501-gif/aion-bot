import os
import requests
from flask import Flask, request, jsonify

app = Flask(__name__)

TOKEN = os.getenv("TELEGRAM_TOKEN")
API_URL = f"https://api.telegram.org/bot{TOKEN}" if TOKEN else None

USER_STATE = {}

BTN_BIOTIME = "🧬 BioTime"
BTN_SLEEP = "💤 Sleep"
BTN_CNS = "🧠 CNS"
BTN_RECOVERY = "🔥 Recovery"
BTN_PRESSURE = "🫀 Pressure"
BTN_INFO = "ℹ️ Info"


def send(chat_id, text, remove_keyboard=False):
    if not API_URL:
        return

    payload = {
        "chat_id": chat_id,
        "text": text
    }

    if remove_keyboard:
        payload["reply_markup"] = {"remove_keyboard": True}

    requests.post(f"{API_URL}/sendMessage", json=payload, timeout=10)


@app.get("/")
def home():
    return "AION is alive 🚀", 200


@app.post("/webhook")
def webhook():
    update = request.get_json()
    message = update.get("message", {})
    chat_id = message.get("chat", {}).get("id")
    text = (message.get("text") or "").strip()

    if not chat_id:
        return jsonify({"ok": True})

    # /start — убираем клавиатуру
    if text == "/start":
        USER_STATE.pop(chat_id, None)

        send(chat_id,
             "AION — система управления скоростью\n"
             "биологического износа, основанная на\n"
             "анализе твоей физиологии.",
             remove_keyboard=True)

        send(chat_id, "Напишите название модуля:\n"
                      "BioTime / Sleep / CNS / Recovery / Pressure / Info")
        return jsonify({"ok": True})

    # BioTime ввод
    if USER_STATE.get(chat_id) == "biotime":
        parts = text.split()

        if len(parts) != 6:
            send(chat_id, "Введите 6 чисел. Пример:\n7 6 8 0 0 1")
            return jsonify({"ok": True})

        try:
            sleep, stress, recovery, p, d, r = map(float, parts)
        except:
            send(chat_id, "Ошибка формата. Только числа.")
            return jsonify({"ok": True})

        score = round((sleep*1.2 + recovery*1.2 - stress) - p - d - r, 1)

        send(chat_id, f"🧬 BioTime = {score}")
        USER_STATE.pop(chat_id, None)
        return jsonify({"ok": True})

    # Текстовая обработка
    if text.lower() == "biotime":
        USER_STATE[chat_id] = "biotime"
        send(chat_id, "Введите 6 чисел через пробел.")
        return jsonify({"ok": True})

    if text.lower() == "sleep":
        send(chat_id, "💤 Sleep модуль.")
        return jsonify({"ok": True})

    if text.lower() == "cns":
        send(chat_id, "🧠 CNS модуль.")
        return jsonify({"ok": True})

    if text.lower() == "recovery":
        send(chat_id, "🔥 Recovery модуль.")
        return jsonify({"ok": True})

    if text.lower() == "pressure":
        send(chat_id, "🫀 Pressure модуль.")
        return jsonify({"ok": True})

    if text.lower() == "info":
        send(chat_id,
             "ℹ️ AION\n\n"
             "🧬 BioTime — оценка восстановления\n"
             "🫀 Pressure — давление\n"
             "💤 Sleep — сон\n"
             "🧠 CNS — нервная система\n"
             "🔥 Recovery — восстановление")
        return jsonify({"ok": True})

    send(chat_id, "Введите название модуля.")
    return jsonify({"ok": True})


if __name__ == "__main__":
    port = int(os.getenv("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
  