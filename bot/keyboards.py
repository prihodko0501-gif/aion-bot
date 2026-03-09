import os
import requests
from flask import Flask, request, jsonify, send_from_directory

app = Flask(__name__)

TOKEN = os.environ.get("TELEGRAM_TOKEN")
API = f"https://api.telegram.org/bot{TOKEN}" if TOKEN else None

WEBAPP_URL = "https://aion-bot.onrender.com/miniapp"

# demo store
data_store = {
    "biotime": None,
    "sleep": None,
    "stress": None,
    "recovery": None,
    "pressure": None,
}

# ---------------------------
# ROOT
# ---------------------------

@app.route("/")
def home():
    return "AION is alive 🚀", 200


# ---------------------------
# MINI APP
# ---------------------------

@app.route("/miniapp")
def miniapp():
    return send_from_directory("templates", "miniapp.html")


# ---------------------------
# DASHBOARD API
# ---------------------------

@app.route("/api/dashboard")
def api_dashboard():
    return jsonify({
        "data": {
            "biotime": data_store["biotime"],
            "sleep": data_store["sleep"],
            "stress": data_store["stress"],
            "recovery": data_store["recovery"],
            "pressure": data_store["pressure"],
        }
    })


# ---------------------------
# DEMO SEED
# ---------------------------

@app.route("/api/demo-seed")
def api_demo_seed():
    data_store["biotime"] = 8.4
    data_store["sleep"] = 92
    data_store["stress"] = 27
    data_store["recovery"] = 78
    data_store["pressure"] = "124/76"

    return jsonify({
        "status": "demo data inserted",
        "data": {
            "biotime": data_store["biotime"],
            "sleep": data_store["sleep"],
            "stress": data_store["stress"],
            "recovery": data_store["recovery"],
            "pressure": data_store["pressure"],
        }
    })


# ---------------------------
# WEBHOOK
# ---------------------------

@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.get_json(silent=True)

    if not data:
        return {"ok": True}

    message = data.get("message")
    if not message:
        return {"ok": True}

    chat_id = message["chat"]["id"]
    text = (message.get("text") or "").strip()

    if text == "/start" and API:
        try:
            # 1) приветствие
            requests.post(
                f"{API}/sendMessage",
                json={
                    "chat_id": chat_id,
                    "text": "AION system online 🚀\n\nНажми кнопку ниже, чтобы открыть Mini App.",
                    "reply_markup": {
                        "inline_keyboard": [
                            [
                                {
                                    "text": "🧬 Open AION",
                                    "web_app": {"url": WEBAPP_URL}
                                }
                            ],
                            [
                                {
                                    "text": "📥 Загрузить demo data",
                                    "url": "https://aion-bot.onrender.com/api/demo-seed"
                                }
                            ]
                        ]
                    }
                },
                timeout=15
            )
        except Exception as e:
            print("sendMessage error:", repr(e))

    return {"ok": True}


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)