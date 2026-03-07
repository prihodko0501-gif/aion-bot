import os
import requests
from flask import Flask, request

app = Flask(__name__)

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
TELEGRAM_API_URL = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}"

# ссылка на твою картинку
PHOTO_URL = "https://raw.githubusercontent.com/prihodko0501-gif/aion-bot/refs/heads/main/9C9D1C07-7426-4DDC-84DD-A76E6AC20138.png"


def send_welcome(chat_id):

    text = """
Система AION разработана
как глобальная платформа,
измеряющая биологическое
время и помогающая управлять
скоростью жизни
"""

    requests.post(
        f"{TELEGRAM_API_URL}/sendPhoto",
        json={
            "chat_id": chat_id,
            "photo": PHOTO_URL,
            "caption": text
        }
    )


@app.route("/")
def index():
    return "AION bot running"


@app.route("/webhook", methods=["POST"])
def webhook():

    update = request.get_json()

    if "message" in update:

        chat_id = update["message"]["chat"]["id"]
        text = update["message"].get("text", "")

        if text == "/start":
            send_welcome(chat_id)

    return "ok", 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)