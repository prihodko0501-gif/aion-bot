import os
import requests
from flask import Flask, request

app = Flask(__name__)

TOKEN = os.environ.get("TELEGRAM_TOKEN")
TELEGRAM_API = f"https://api.telegram.org/bot{TOKEN}"

IMAGE_URL = "https://raw.githubusercontent.com/prihodko0501-gif/aion-bot/main/aion_logo.png"


@app.route("/")
def home():
    return "AION system online"


def send_photo(chat_id):
    requests.post(
        f"{TELEGRAM_API}/sendPhoto",
        data={
            "chat_id": chat_id,
            "photo": IMAGE_URL,
            "caption": "Upgrade System"
        }
    )


@app.route("/webhook", methods=["POST"])
def webhook():

    data = request.get_json()

    if "message" in data:

        chat_id = data["message"]["chat"]["id"]
        text = data["message"].get("text")

        if text == "/start":
            send_photo(chat_id)

    return "ok"