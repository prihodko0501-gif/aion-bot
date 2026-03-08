import os
import requests
from flask import Flask, request

app = Flask(__name__)

TOKEN = os.environ.get("TELEGRAM_TOKEN")
TELEGRAM_API = f"https://api.telegram.org/bot{TOKEN}"

IMAGE_URL = "https://raw.githubusercontent.com/prihodko0501-gif/aion-bot/main/B0AEE152-2F0A-4DD9-8A25-D25C1D6AFE54.png"


def send_photo(chat_id):
    url = f"{TELEGRAM_API}/sendPhoto"
    payload = {
        "chat_id": chat_id,
        "photo": IMAGE_URL,
        "caption": "Upgrade System"
    }
    requests.post(url, data=payload)


@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.get_json()
    if "message" in data:
        chat_id = data["message"]["chat"]["id"]
        text = data["message"].get("text", "")
        if text == "/start":
            send_photo(chat_id)
    return "ok"


@app.route("/")
def home():
    return "AION system online"