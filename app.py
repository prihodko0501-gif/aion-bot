import os
import requests
from flask import Flask, request, jsonify, send_from_directory

app = Flask(__name__)

TOKEN = os.environ.get("TELEGRAM_TOKEN")
API = f"https://api.telegram.org/bot{TOKEN}"

IMAGE_URL = "https://raw.githubusercontent.com/prihodko0501-gif/aion-bot/main/B0AEE152-2F0A-4DD9-8A25-D25C1D6AFE54.jpeg"


@app.route("/")
def home():
    return send_from_directory("webapp", "index.html")


@app.route("/app")
def mini_app():
    return send_from_directory("webapp", "index.html")


@app.route("/webhook", methods=["POST"])
def webhook():

    data = request.get_json()

    if "message" not in data:
        return {"ok": True}

    chat_id = data["message"]["chat"]["id"]
    text = data["message"].get("text", "")

    if text == "/start":

        requests.post(
            f"{API}/sendPhoto",
            json={
                "chat_id": chat_id,
                "photo": IMAGE_URL,
                "caption": "AION\nBiological Upgrade System\n\nСистема инициализирована."
            }
        )

    return {"ok": True}