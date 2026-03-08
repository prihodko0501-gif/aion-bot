import os
import requests
from flask import Flask, request, send_from_directory, jsonify

app = Flask(__name__)

TOKEN = os.environ.get("TELEGRAM_TOKEN")
API = f"https://api.telegram.org/bot{TOKEN}"

IMAGE_URL = "https://raw.githubusercontent.com/prihodko0501-gif/aion-bot/miniapp-structure/B0AEE152-2F0A-4DD9-8A25-D25C1D6AFE54.jpeg"


@app.get("/")
def home():
    return "AION is alive 🚀", 200


@app.get("/app")
def mini_app():
    return send_from_directory("webapp", "index.html")


@app.post("/webhook")
def webhook():
    data = request.get_json(silent=True) or {}

    message = data.get("message")
    if not message:
        return jsonify({"ok": True}), 200

    chat_id = message["chat"]["id"]
    text = message.get("text", "")

    if text == "/start":
        requests.post(
            f"{API}/sendPhoto",
            json={
                "chat_id": chat_id,
                "photo": IMAGE_URL,
                "caption": "Upgrade System"
            },
            timeout=20
        )

    return jsonify({"ok": True}), 200