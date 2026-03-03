import os
import logging
from flask import Flask, request
import requests

TOKEN = os.getenv("BOT_TOKEN")
URL = f"https://api.telegram.org/bot{TOKEN}"

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)


# ========================
# SEND MESSAGE
# ========================
def send_message(chat_id, text, keyboard=None):
    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "HTML"
    }

    if keyboard:
        payload["reply_markup"] = keyboard

    requests.post(f"{URL}/sendMessage", json=payload)


# ========================
# MAIN MENU
# ========================
def main_menu():
    return {
        "inline_keyboard": [
            [{"text": "🧬 BioTime", "callback_data": "biotime"}],
            [
                {"text": "💤 Sleep", "callback_data": "sleep"},
                {"text": "🧠 CNS", "callback_data": "cns"}
            ],
            [
                {"text": "🔥 Recovery", "callback_data": "recovery"},
                {"text": "❤️ Pressure", "callback_data": "pressure"}
            ],
            [{"text": "ℹ️ Info", "callback_data": "info"}]
        ]
    }


# ========================
# START
# ========================
@app.route("/", methods=["POST"])
def webhook():
    data = request.json

    # ----------------------
    # MESSAGE
    # ----------------------
    if "message" in data:
        chat_id = data["message"]["chat"]["id"]

        if data["message"].get("text") == "/start":
            send_message(
                chat_id,
                "AION — система управления биологическим возрастом.\n\nВыберите модуль:",
                main_menu()
            )

    # ----------------------
    # CALLBACK
    # ----------------------
    if "callback_query" in data:
        callback = data["callback_query"]
        chat_id = callback["message"]["chat"]["id"]
        data_value = callback["data"]

        # обязательно отвечаем Telegram
        requests.post(
            f"{URL}/answerCallbackQuery",
            json={"callback_query_id": callback["id"]}
        )

        # ====== ROUTING ======
        if data_value == "biotime":
            send_message(chat_id, "🧬 Модуль BioTime активирован.\nРасчёт скоро будет доступен.")

        elif data_value == "sleep":
            send_message(chat_id, "💤 Sleep — модуль в разработке.")

        elif data_value == "cns":
            send_message(chat_id, "🧠 CNS — модуль в разработке.")

        elif data_value == "recovery":
            send_message(chat_id, "🔥 Recovery — модуль в разработке.")

        elif data_value == "pressure":
            send_message(chat_id, "❤️ Pressure — модуль в разработке.")

        elif data_value == "info":
            send_message(chat_id, "ℹ️ AION — Biological Upgrade System.")

    return "ok", 200


if __name__ == "__main__":
    app.run()