import os
import requests
from flask import Flask, request, jsonify, send_from_directory

app = Flask(__name__)

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
API = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}"

BASE_URL = "https://aion-bot.onrender.com"


# -----------------------------
# ROOT
# -----------------------------

@app.route("/")
def home():
    return "AION is alive 🚀"


# -----------------------------
# MINI APP
# -----------------------------

@app.route("/miniapp")
def miniapp():
    return send_from_directory(".", "miniapp.html")


# -----------------------------
# DEMO DATA
# -----------------------------

demo_data = {
    "biotime": 8.4,
    "sleep": 92,
    "stress": 27,
    "recovery": 78,
    "pressure": "124/76"
}


@app.route("/demo", methods=["POST"])
def demo():
    return jsonify({
        "data": demo_data,
        "status": "demo data inserted"
    })


@app.route("/data")
def get_data():
    return jsonify({
        "data": demo_data
    })


# -----------------------------
# TELEGRAM WEBHOOK
# -----------------------------

@app.route("/webhook", methods=["POST"])
def webhook():

    data = request.json

    if not data:
        return {"ok": True}

    message = data.get("message")

    if not message:
        return {"ok": True}

    chat_id = message["chat"]["id"]
    text = (message.get("text") or "").strip()

    if text == "/start":

        requests.post(
            f"{API}/sendMessage",
            json={
                "chat_id": chat_id,
                "text": "AION system online 🚀\n\nНажми кнопку ниже, чтобы открыть Mini App.",
                "reply_markup": {
                    "inline_keyboard": [
                        [
                            {
                                "text": "🚀 Open AION",
                                "web_app": {
                                    "url": f"{BASE_URL}/miniapp"
                                }
                            }
                        ],
                        [
                            {
                                "text": "📥 Загрузить demo data",
                                "url": f"{BASE_URL}/demo"
                            }
                        ]
                    ]
                }
            }
        )

    return {"ok": True}


# -----------------------------
# SERVER START
# -----------------------------

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)