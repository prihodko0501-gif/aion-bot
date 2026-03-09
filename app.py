import os
import requests
from flask import Flask, request, send_from_directory, render_template

app = Flask(__name__)

TOKEN = os.environ.get("TELEGRAM_TOKEN")
API = f"https://api.telegram.org/bot{TOKEN}"

IMAGE_URL = "https://raw.githubusercontent.com/prihodko0501-gif/aion-bot/main/563CC010-50CF-4E76-9C55-A3CEA18351D9.png"


@app.route("/")
def home():
    return "AION is alive 🚀", 200


@app.route("/miniapp")
def miniapp():
    return render_template("miniapp.html")


@app.route("/app")
def mini_app():
    return send_from_directory("webapp", "index.html")


@app.route("/api/dashboard")
def api_dashboard():
    return {
        "biotime": 8.4,
        "sleep": 92,
        "stress": 27,
        "recovery": 78,
        "pressure": "124/76"
    }


@app.route("/api/history")
def api_history():
    return {
        "data": [
            {"date": "2026-03-01", "biotime": 7.8},
            {"date": "2026-03-02", "biotime": 8.0},
            {"date": "2026-03-03", "biotime": 8.2},
            {"date": "2026-03-04", "biotime": 8.3},
            {"date": "2026-03-05", "biotime": 8.1},
            {"date": "2026-03-06", "biotime": 8.4},
            {"date": "2026-03-07", "biotime": 8.5}
        ]
    }


@app.route("/api/sleep")
def api_sleep():
    return {
        "score": 92,
        "duration": "7h 25m",
        "latency": "5m",
        "stability": "94%"
    }


@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.get_json(silent=True)

    if not data:
        return {"ok": True}

    message = data.get("message")
    if not message:
        return {"ok": True}

    chat_id = message["chat"]["id"]
    text = message.get("text", "")

    if text == "/start":
        try:
            requests.post(
                f"{API}/sendPhoto",
                json={
                    "chat_id": chat_id,
                    "photo": IMAGE_URL,
                    "caption": "UPGRADE SYSTEM"
                },
                timeout=15
            )
        except Exception as e:
            print("sendPhoto error:", repr(e))

    return {"ok": True}


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)