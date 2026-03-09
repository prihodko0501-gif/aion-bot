import os
import requests
from flask import Flask, request, jsonify, send_from_directory

app = Flask(__name__)

TOKEN = os.environ.get("TELEGRAM_TOKEN")
API = f"https://api.telegram.org/bot{TOKEN}"

# ---------------------------
# DEMO DATA
# ---------------------------

data_store = {
    "biotime": None,
    "sleep": None,
    "stress": None,
    "recovery": None,
    "pressure": None
}

# ---------------------------
# ROOT
# ---------------------------

@app.route("/")
def home():
    return "AION is alive 🚀"


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
def dashboard():

    return jsonify({
        "data": {
            "biotime": data_store["biotime"],
            "sleep": data_store["sleep"],
            "stress": data_store["stress"],
            "recovery": data_store["recovery"],
            "pressure": data_store["pressure"]
        }
    })


# ---------------------------
# DEMO DATA SEED
# ---------------------------

@app.route("/api/demo-seed")
def seed():

    data_store["biotime"] = 8.4
    data_store["sleep"] = 92
    data_store["stress"] = 27
    data_store["recovery"] = 78
    data_store["pressure"] = "124/76"

    return jsonify({
        "status": "demo data inserted",
        "data": data_store
    })


# ---------------------------
# TELEGRAM WEBHOOK
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
    text = message.get("text", "")

    if text == "/start":

        requests.post(
            f"{API}/sendMessage",
            json={
                "chat_id": chat_id,
                "text": "AION system online 🚀"
            }
        )

    return {"ok": True}