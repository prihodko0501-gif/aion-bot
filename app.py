import os
import requests
from flask import Flask, request

app = Flask(__name__)

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
TELEGRAM_API_URL = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}"

CHAT_IMAGE_URL = "https://raw.githubusercontent.com/prihodko0501-gif/aion-bot/main/9D9FDFD2-B4BA-466A-B297-D8919BC296B9.png"
APP_IMAGE_URL = "https://raw.githubusercontent.com/prihodko0501-gif/aion-bot/main/563CC010-50CF-4E76-9C55-A3CEA18351D9.png"


@app.route("/")
def home():
    return "AION BOT WORKING", 200


@app.route("/app")
def mini_app():
    return f"""
    <html>
    <head>
        <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
        <style>
            html, body {{
                margin: 0;
                padding: 0;
                width: 100%;
                height: 100%;
                overflow: hidden;
                background: black;
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
            <img src="{APP_IMAGE_URL}" alt="AION">
        </div>
    </body>
    </html>
    """


@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.get_json(silent=True) or {}

    if "message" in data:
        chat_id = data["message"]["chat"]["id"]
        text = data["message"].get("text", "")

        if text == "/start":
            requests.post(
                f"{TELEGRAM_API_URL}/sendPhoto",
                json={
                    "chat_id": chat_id,
                    "photo": CHAT_IMAGE_URL,
                    "caption": "Upgrade System"
                },
                timeout=15,
            )

    return "ok", 200


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "10000"))
    app.run(host="0.0.0.0", port=port)