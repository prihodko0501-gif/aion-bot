import os
import time
import requests
from flask import Flask, request

app = Flask(__name__)

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
TELEGRAM_API_URL = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}"

IMAGE_URL = "https://raw.githubusercontent.com/prihodko0501-gif/aion-bot/main/563CC010-50CF-4E76-9C55-A3CEA18351D9.png"


@app.route("/")
def home():
    return "AION BOT WORKING", 200


@app.route("/app")
def mini_app():
    return f"""
    <html>
    <head>
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
            html, body {{
                margin: 0;
                padding: 0;
                height: 100%;
                background: black;
                overflow: hidden;
            }}

            .screen {{
                width: 100%;
                height: 100vh;
            }}

            .screen img {{
                width: 100%;
                height: 100%;
                object-fit: cover;
                display: block;
            }}
        </style>
    </head>
    <body>
        <div class="screen">
            <img src="{IMAGE_URL}" alt="AION">
        </div>
    </body>
    </html>
    """


def send_message(chat_id, text):
    requests.post(
        f"{TELEGRAM_API_URL}/sendMessage",
        json={
            "chat_id": chat_id,
            "text": text
        }
    )


def send_start_screen(chat_id):
    keyboard = {
        "inline_keyboard": [
            [
                {
                    "text": "Open AION",
                    "web_app": {
                        "url": "https://aion-bot.onrender.com/app"
                    }
                }
            ]
        ]
    }

    requests.post(
        f"{TELEGRAM_API_URL}/sendPhoto",
        json={
            "chat_id": chat_id,
            "photo": IMAGE_URL,
            "caption": "AION — Biological Upgrade System",
            "reply_markup": keyboard
        }
    )


@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.get_json(silent=True) or {}

    if "message" in data:
        chat_id = data["message"]["chat"]["id"]
        text = data["message"].get("text", "")

        if text == "/start":
            send_message(chat_id, "AION\nBiological Upgrade System\n\nИнициализация системы...")
            time.sleep(2)

            send_message(chat_id, "Анализ биологических параметров...")
            time.sleep(2)

            send_message(chat_id, "Система готова")
            time.sleep(2)

            send_start_screen(chat_id)

    return "ok", 200


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "10000"))
    app.run(host="0.0.0.0", port=port)