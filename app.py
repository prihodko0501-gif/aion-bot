import os
from datetime import datetime, timedelta
import requests
from flask import Flask, request, jsonify, send_from_directory

app = Flask(__name__)

TOKEN = os.environ.get("TELEGRAM_TOKEN")
API = f"https://api.telegram.org/bot{TOKEN}" if TOKEN else None

WEBAPP_URL = "https://aion-bot.onrender.com/miniapp"

# ---------------------------
# DEMO DATA STORE
# ---------------------------

data_store = {
    "biotime": None,
    "sleep": None,
    "stress": None,
    "recovery": None,
    "pressure": None,
}

history_store = []


def add_history_entry(biotime, sleep, stress, recovery, pressure, dt=None):
    if dt is None:
        dt = datetime.utcnow()

    history_store.append({
        "date": dt.strftime("%Y-%m-%d"),
        "biotime": biotime,
        "sleep": sleep,
        "stress": stress,
        "recovery": recovery,
        "pressure": pressure,
        "created_at": dt.isoformat(),
    })


def seed_demo_history():
    history_store.clear()

    base = datetime.utcnow()
    demo = [
        (7.8, 88, 31, 74, "126/78"),
        (8.0, 89, 30, 75, "125/78"),
        (8.1, 90, 29, 76, "125/77"),
        (8.2, 91, 28, 76, "124/77"),
        (8.3, 91, 28, 77, "124/76"),
        (8.4, 92, 27, 78, "124/76"),
        (8.4, 92, 27, 78, "124/76"),
    ]

    for i, row in enumerate(demo):
        dt = base - timedelta(days=(len(demo) - 1 - i))
        add_history_entry(*row, dt=dt)


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
# HISTORY API
# ---------------------------

@app.route("/api/history")
def api_history():
    try:
        days = int(request.args.get("days", 7))
    except Exception:
        days = 7

    if days not in (7, 30, 90):
        days = 7

    result = history_store[-days:]

    return jsonify({
        "days": days,
        "data": result
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

    seed_demo_history()

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