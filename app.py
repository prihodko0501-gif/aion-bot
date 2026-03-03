import os
import requests
from flask import Flask, request, jsonify

app = Flask(__name__)

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
API_URL = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}"


# ========================
# TELEGRAM HELPERS
# ========================

def send_message(chat_id, text, reply_markup=None):
    payload = {
        "chat_id": chat_id,
        "text": text
    }
    if reply_markup:
        payload["reply_markup"] = reply_markup

    requests.post(f"{API_URL}/sendMessage", json=payload)


def answer_callback(callback_query_id):
    requests.post(f"{API_URL}/answerCallbackQuery", json={
        "callback_query_id": callback_query_id
    })


# ========================
# UI
# ========================

def main_menu():
    return {
        "inline_keyboard": [
            [{"text": "🧬 BioTime", "callback_data": "biotime"}],
            [{"text": "💤 Sleep", "callback_data": "sleep"},
             {"text": "🧠 CNS", "callback_data": "cns"}],
            [{"text": "🔥 Recovery", "callback_data": "recovery"},
             {"text": "🫀 Pressure", "callback_data": "pressure"}],
            [{"text": "ℹ️ Info", "callback_data": "info"}],
        ]
    }


# ========================
# ROUTES
# ========================

@app.route("/", methods=["GET"])
def home():
    return "AION is running", 200


@app.route("/webhook", methods=["POST"])
def webhook():
    update = request.get_json()

    # ===== CALLBACK =====
    if "callback_query" in update:
        callback = update["callback_query"]
        chat_id = callback["message"]["chat"]["id"]
        data = callback["data"]

        answer_callback(callback["id"])

        if data == "biotime":
            send_message(chat_id, "🧬 BioTime модуль скоро будет доступен.")
        elif data == "sleep":
            send_message(chat_id, "💤 Sleep модуль скоро будет доступен.")
        elif data == "cns":
            send_message(chat_id, "🧠 CNS модуль скоро будет доступен.")
        elif data == "recovery":
            send_message(chat_id, "🔥 Recovery модуль скоро будет доступен.")
        elif data == "pressure":
            send_message(chat_id, "🫀 Pressure модуль скоро будет доступен.")
        elif data == "info":
            send_message(chat_id, "ℹ️ AION — система управления биологическим возрастом.")

        return jsonify({"ok": True}), 200

    # ===== MESSAGE =====
    if "message" in update:
        message = update["message"]
        chat_id = message["chat"]["id"]
        text = message.get("text", "")

        if text.startswith("/start"):
            send_message(chat_id,
                         "AION — система управления скоростью биологического износа.\n\nВыберите модуль:",
                         main_menu())

    return jsonify({"ok": True}), 200