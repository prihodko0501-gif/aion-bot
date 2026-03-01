import os
import requests
from flask import Flask, request, jsonify

app = Flask(__name__)

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
TELEGRAM_API_URL = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}" if TELEGRAM_TOKEN else None

# Простое состояние: ждём ввод 6 чисел для BioTime
USER_STATE = {}  # chat_id -> {"step": "biotime_input"}


# ====== КНОПКИ КАК НА ФОТО (Reply keyboard) ======
BTN_BIOTIME = "🧬 BioTime"
BTN_SLEEP = "💤 Sleep"
BTN_CNS = "🧠 CNS"
BTN_RECOVERY = "🔥 Recovery"
BTN_PRESSURE = "❤️ Pressure"
BTN_INFO = "ℹ️ Info"


def main_menu_reply():
    # ReplyKeyboardMarkup (как на твоём скрине)
    return {
        "keyboard": [
            [{"text": BTN_BIOTIME}],
            [{"text": BTN_SLEEP}, {"text": BTN_CNS}],
            [{"text": BTN_RECOVERY}, {"text": BTN_PRESSURE}],
            [{"text": BTN_INFO}],
        ],
        "resize_keyboard": True,
        "one_time_keyboard": False,
        "is_persistent": True,
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


@app.get("/")
def home():
    return "AION is alive 🚀", 200


@app.post("/webhook")
def webhook():
    if not TELEGRAM_TOKEN:
        return jsonify({"error": "No TELEGRAM_TOKEN"}), 500

    update = request.get_json(silent=True) or {}
    message = update.get("message") or {}

    chat_id = message.get("chat", {}).get("id")
    text = (message.get("text") or "").strip()

    if not chat_id:
        return jsonify({"ok": True})

    # /start — показываем привет и меню
    if text == "/start":
        USER_STATE.pop(chat_id, None)
        send_message(
            chat_id,
            "AION — система управления скоростью биологического износа, основанная на анализе твоей физиологии.\n\n"
            "Выберите модуль:",
            reply_markup=main_menu_reply(),
        )
        return jsonify({"ok": True})

    # Если мы ждём ввод для BioTime
    if USER_STATE.get(chat_id, {}).get("step") == "biotime_input":
        parts = text.split()
        if len(parts) != 6:
            send_message(chat_id, "Нужно 6 чисел. Пример: 7 6 8 0 0 1", reply_markup=main_menu_reply())
            return jsonify({"ok": True})

        try:
            sleep = float(parts[0])
            stress = float(parts[1])
            recovery = float(parts[2])
            pressure_penalty = float(parts[3])
            drop_penalty = float(parts[4])
            risk_penalty = float(parts[5])
        except Exception:
            send_message(chat_id, "Ошибка формата. Введи 6 чисел через пробел.", reply_markup=main_menu_reply())
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
            reply_markup=main_menu_reply(),
        )

        USER_STATE.pop(chat_id, None)
        return jsonify({"ok": True})

    # ====== ОБРАБОТКА КНОПОК (ПО ТЕКСТУ) ======
    if text == BTN_BIOTIME:
        USER_STATE[chat_id] = {"step": "biotime_input"}
        send_message(chat_id, "🧬 BioTime модуль.\n\nВведи 6 чисел через пробел:\nSleep Stress Recovery PressurePenalty DropPenalty RiskPenalty\n\nПример:\n7 6 8 0 0 1",
                     reply_markup=main_menu_reply())
        return jsonify({"ok": True})

    if text == BTN_SLEEP:
        send_message(chat_id, "💤 Sleep модуль.", reply_markup=main_menu_reply())
        return jsonify({"ok": True})

    if text == BTN_CNS:
        send_message(chat_id, "🧠 CNS модуль.", reply_markup=main_menu_reply())
        return jsonify({"ok": True})

    if text == BTN_RECOVERY:
        send_message(chat_id, "🔥 Recovery модуль.", reply_markup=main_menu_reply())
        return jsonify({"ok": True})

    if text == BTN_PRESSURE:
        send_message(chat_id, "❤️ Pressure модуль.", reply_markup=main_menu_reply())
        return jsonify({"ok": True})

    if text == BTN_INFO:
        send_message(
            chat_id,
            "ℹ️ AION\n"
            "AION — система управления скоростью биологического износа.\n\n"
            "🧬 BioTime — интегральная оценка восстановления.\n"
            "❤️ Pressure — давление и пульс.\n"
            "💤 Sleep — сон.\n"
            "🧠 CNS — нервная система.\n"
            "🔥 Recovery — восстановление.\n\n"
            "Выбирай модуль в меню.",
            reply_markup=main_menu_reply(),
        )
        return jsonify({"ok": True})

    # Любой другой текст — просто вернём меню
    send_message(chat_id, "Выберите модуль:", reply_markup=main_menu_reply())
    return jsonify({"ok": True})


# В Render через gunicorn этот блок не нужен, но для локального запуска пусть будет
if __name__ == "__main__":
    port = int(os.environ.get("PORT", "8080"))
    app.run(host="0.0.0.0", port=port)