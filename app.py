import os
import requests
from flask import Flask, request, jsonify

app = Flask(__name__)

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
API = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}" if TELEGRAM_TOKEN else None

USER_STATE = {}  # chat_id -> {"step": "biotime_input"}

# ====== КНОПКИ КАК НА ФОТО + "Перезапуск" ======
def main_menu_keyboard():
    return {
        "keyboard": [
            [{"text": "💤 Sleep"}, {"text": "🧠 CNS"}],
            [{"text": "🔥 Recovery"}, {"text": "❤️ Pressure"}],
            [{"text": "ℹ️ Info"}],
            [{"text": "🧬 BioTime"}],
            [{"text": "🔄 Перезапуск"}],
        ],
        "resize_keyboard": True,
        "one_time_keyboard": False,
        "is_persistent": True
    }

def send_message(chat_id: int, text: str, reply_markup=None):
    if not API:
        return
    payload = {"chat_id": chat_id, "text": text}
    if reply_markup:
        payload["reply_markup"] = reply_markup
    try:
        requests.post(f"{API}/sendMessage", json=payload, timeout=10)
    except Exception:
        pass

def show_menu(chat_id: int):
    send_message(
        chat_id,
        "AION — система управления скоростью биологического износа, основанная на анализе твоей физиологии.\n\n"
        "Выберите модуль:",
        reply_markup=main_menu_keyboard()
    )

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
        return jsonify({"ok": True}), 200

    # /start или Перезапуск
    if text in ("/start", "🔄 Перезапуск"):
        USER_STATE.pop(chat_id, None)
        show_menu(chat_id)
        return jsonify({"ok": True}), 200

    # ждём ввод для BioTime
    if USER_STATE.get(chat_id, {}).get("step") == "biotime_input":
        parts = text.split()
        if len(parts) != 6:
            send_message(chat_id, "Нужно 6 чисел. Пример: 7 6 8 0 0 1", reply_markup=main_menu_keyboard())
            return jsonify({"ok": True}), 200

        try:
            sleep = float(parts[0])
            stress = float(parts[1])
            recovery = float(parts[2])
            pressure_penalty = float(parts[3])
            drop_penalty = float(parts[4])
            risk_penalty = float(parts[5])
        except Exception:
            send_message(chat_id, "Ошибка формата. Введи 6 чисел через пробел.", reply_markup=main_menu_keyboard())
            return jsonify({"ok": True}), 200

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
            reply_markup=main_menu_keyboard()
        )
        USER_STATE.pop(chat_id, None)
        return jsonify({"ok": True}), 200

    # обработка кнопок (это обычный текст)
    if text == "🧬 BioTime":
        USER_STATE[chat_id] = {"step": "biotime_input"}
        send_message(
            chat_id,
            "🧬 BioTime расчёт\n\n"
            "Введи 6 чисел через пробел:\n"
            "Sleep Stress Recovery PressurePenalty DropPenalty RiskPenalty\n\n"
            "Пример:\n"
            "7 6 8 0 0 1",
            reply_markup=main_menu_keyboard()
        )
        return jsonify({"ok": True}), 200

    if text == "💤 Sleep":
        send_message(chat_id, "💤 Sleep модуль.", reply_markup=main_menu_keyboard
