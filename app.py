import os
import requests
from flask import Flask, request, jsonify

app = Flask(__name__)

TOKEN = os.getenv("TELEGRAM_TOKEN")
API_URL = f"https://api.telegram.org/bot{TOKEN}" if TOKEN else None

# =========================
# КНОПКИ (как на фото)
# =========================
BTN_BIOTIME = "🧬 BioTime"
BTN_SLEEP = "💤 Sleep"
BTN_CNS = "🧠 CNS"
BTN_RECOVERY = "🔥 Recovery"
BTN_PRESSURE = "🫀 Pressure"
BTN_INFO = "ℹ️ Info"

# состояние пользователя
USER_STATE = {}


# =========================
# КЛАВИАТУРА
# =========================
def main_keyboard():
    return {
        "keyboard": [
            [{"text": BTN_BIOTIME}],
            [{"text": BTN_SLEEP}, {"text": BTN_CNS}],
            [{"text": BTN_RECOVERY}, {"text": BTN_PRESSURE}],
            [{"text": BTN_INFO}],
        ],
        "resize_keyboard": True,
        "is_persistent": True
    }


# =========================
# ОТПРАВКА СООБЩЕНИЙ
# =========================
def send(chat_id, text):
    if not API_URL:
        return

    requests.post(
        f"{API_URL}/sendMessage",
        json={
            "chat_id": chat_id,
            "text": text,
            "reply_markup": main_keyboard()
        },
        timeout=10
    )


# =========================
# HEALTH CHECK
# =========================
@app.get("/")
def home():
    return "AION is alive 🚀", 200


# =========================
# WEBHOOK
# =========================
@app.post("/webhook")
def webhook():
    update = request.get_json()
    message = update.get("message", {})
    chat_id = message.get("chat", {}).get("id")
    text = (message.get("text") or "").strip()

    if not chat_id:
        return jsonify({"ok": True})

    # =====================
    # /start (БЛОКАМИ)
    # =====================
    if text == "/start":
        USER_STATE.pop(chat_id, None)

        send(chat_id,
             "AION — система управления скоростью\n"
             "биологического износа, основанная на\n"
             "анализе твоей физиологии.")

        send(chat_id, "Выберите модуль:")
        return jsonify({"ok": True})

    # =====================
    # BIO TIME ВВОД
    # =====================
    if USER_STATE.get(chat_id) == "biotime":
        parts = text.split()

        if len(parts) != 6:
            send(chat_id, "Введите 6 чисел. Пример:\n7 6 8 0 0 1")
            return jsonify({"ok": True})

        try:
            sleep, stress, recovery, p, d, r = map(float, parts)
        except:
            send(chat_id, "Ошибка формата. Только числа через пробел.")
            return jsonify({"ok": True})

        score = round((sleep*1.2 + recovery*1.2 - stress) - p - d - r, 1)

        if score < 4:
            status = "🔴 Высокая нагрузка"
        elif score < 8:
            status = "🟠 Средняя нагрузка"
        elif score <= 11:
            status = "🟡 Норма"
        else:
            status = "🟢 Оптимум"

        send(chat_id,
             f"🧬 BioTime = {score}\n"
             f"{status}")

        USER_STATE.pop(chat_id, None)
        return jsonify({"ok": True})

    # =====================
    # КНОПКИ
    # =====================
    if text == BTN_BIOTIME:
        USER_STATE[chat_id] = "biotime"
        send(chat_id,
             "🧬 BioTime модуль.\n\n"
             "Введите 6 чисел:\n"
             "Sleep Stress Recovery Pressure Drop Risk")
        return jsonify({"ok": True})

    if text == BTN_SLEEP:
        send(chat_id, "💤 Sleep модуль.")
        return jsonify({"ok": True})

    if text == BTN_CNS:
        send(chat_id, "🧠 CNS модуль.")
        return jsonify({"ok": True})

    if text == BTN_RECOVERY:
        send(chat_id, "🔥 Recovery модуль.")
        return jsonify({"ok": True})

    if text == BTN_PRESSURE:
        send(chat_id, "🫀 Pressure модуль.")
        return jsonify({"ok": True})

    if text == BTN_INFO:
        send(chat_id,
             "ℹ️ AION\n\n"
             "🧬 BioTime — интегральная оценка восстановления.\n"
             "🫀 Pressure — давление и пульс.\n"
             "💤 Sleep — сон.\n"
             "🧠 CNS — нервная система.\n"
             "🔥 Recovery — восстановление.\n\n"
             "Выбирайте модуль.")
        return jsonify({"ok": True})

    # если что-то другое
    send(chat_id, "Выберите модуль:")
    return jsonify({"ok": True})


if __name__ == "__main__":
    port = int(os.getenv("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
        
        