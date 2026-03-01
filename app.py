import os
import requests
from flask import Flask, request, jsonify

app = Flask(__name__)

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
API = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}" if TELEGRAM_TOKEN else None

# простое состояние: ждём ввод 6 чисел для BioTime
USER_STATE = {}  # chat_id -> {"step": "biotime_input"}

# ====== КНОПКИ КАК НА ФОТО (Reply Keyboard) ======
def main_menu_keyboard():
    return {
        "keyboard": [
            [{"text": "🧬 BioTime"}],
            [{"text": "💤 Sleep"}, {"text": "🧠 CNS"}],
            [{"text": "🔥 Recovery"}, {"text": "❤️ Pressure"}],
            [{"text": "ℹ️ Info"}],
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

    # /start
    if text == "/start":
        USER_STATE.pop(chat_id, None)
        send_message(
            chat_id,
            "AION — система управления скоростью биологического износа, основанная на анализе твоей физиологии.\n\n"
            "Выберите модуль:",
            reply_markup=main_menu_keyboard()
        )
        return jsonify({"ok": True}), 200

    # если ждём ввод для BioTime
    if USER_STATE.get(chat_id, {}).get("step") == "biotime_input":
        parts = text.split()
        if len(parts) != 6:
            send_message(chat_id, "Нужно 6 чис