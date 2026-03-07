import os
import requests
from flask import Flask, request

TOKEN = os.environ.get("TELEGRAM_TOKEN")
API_URL = f"https://api.telegram.org/bot{TOKEN}"

app = Flask(__name__)

@app.route("/")
def home():
    return "AION BOT WORKING", 200

@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.get_json(silent=True) or {}
    print("TELEGRAM UPDATE:", data, flush=True)

    message = data.get("message", {})
    chat_id = message.get("chat", {}).get("id")
    text = (message.get("text") or "").strip()

    if chat_id and text == "/start":
        requests.post(
            f"{API_URL}/sendMessage",
            json={
                "chat_id": chat_id,
                "text": "AION запущен. Бот на связи."
            },
            timeout=10,
        )

    return "ok", 200

if __name__ == "__main__":
    port = int(os.environ.get("PORT", "10000"))
    app.run(host="0.0.0.0", port=port)