import os
from datetime import datetime, timedelta
import requests
from flask import Flask, request, jsonify, send_from_directory

app = Flask(__name__)

TOKEN = os.environ.get("TELEGRAM_TOKEN")
API = f"https://api.telegram.org/bot{TOKEN}" if TOKEN else None

WEBAPP_URL = "https://aion-bot.onrender.com/miniapp"

# ---------------------------
# MEMORY STORE (текущий MVP)
# ---------------------------

data_store = {
    "biotime": None,
    "sleep": None,
    "stress": None,
    "recovery": None,
    "pressure": None,
}

history_store = []


# ---------------------------
# HELPERS
# ---------------------------

def clamp(value, low, high):
    return max(low, min(high, value))


def parse_float(value):
    if value in (None, "", "null"):
        return None
    try:
        return float(value)
    except Exception:
        return None


def parse_int(value):
    if value in (None, "", "null"):
        return None
    try:
        return int(value)
    except Exception:
        return None


def parse_pressure_string(value):
    """
    Принимает строку вида '124/76'
    Возвращает (124, 76) или (None, None)
    """
    if not value:
        return None, None

    value = str(value).strip().replace(" ", "")
    if "/" not in value:
        return None, None

    parts = value.split("/")
    if len(parts) != 2:
        return None, None

    sys_val = parse_int(parts[0])
    dia_val = parse_int(parts[1])
    return sys_val, dia_val


def pressure_penalty(systolic, diastolic):
    penalty = 0.0

    if systolic is None or diastolic is None:
        return 0.0

    if systolic >= 140:
        penalty += 1.2
    elif systolic >= 130:
        penalty += 0.6
    elif systolic < 100:
        penalty += 0.4

    if diastolic >= 90:
        penalty += 0.8
    elif diastolic >= 85:
        penalty += 0.4
    elif diastolic < 60:
        penalty += 0.3

    return round(penalty, 2)


def compute_biotime(sleep, stress, recovery, pressure=None):
    """
    Простой расчёт для MVP по текущему этапу.
    Проценты 0-100 → шкала 0-10.
    """

    sleep = float(sleep or 0)
    stress = float(stress or 0)
    recovery = float(recovery or 0)

    sleep10 = sleep / 10.0
    stress10 = stress / 10.0
    recovery10 = recovery / 10.0

    systolic, diastolic = parse_pressure_string(pressure)
    p_penalty = pressure_penalty(systolic, diastolic)

    biotime = round((sleep10 * 1.2 + recovery10 * 1.2 - stress10) - p_penalty, 1)
    biotime = clamp(biotime, 0, 12)

    return biotime


def add_history_entry(biotime, sleep, stress, recovery, pressure, dt=None):
    if dt is None:
        dt = datetime.utcnow()

    history_store.append({
        "date": dt.strftime("%Y-%m-%d"),
        "created_at": dt.isoformat(),
        "biotime": biotime,
        "sleep": sleep,
        "stress": stress,
        "recovery": recovery,
        "pressure": pressure,
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


def refresh_dashboard_from_last_history():
    if not history_store:
        data_store["biotime"] = None
        data_store["sleep"] = None
        data_store["stress"] = None
        data_store["recovery"] = None
        data_store["pressure"] = None
        return

    last = history_store[-1]
    data_store["biotime"] = last["biotime"]
    data_store["sleep"] = last["sleep"]
    data_store["stress"] = last["stress"]
    data_store["recovery"] = last["recovery"]
    data_store["pressure"] = last["pressure"]


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
# REAL ENTRY API
# ---------------------------

@app.route("/api/entry", methods=["POST"])
def api_entry():
    payload = request.get_json(silent=True) or {}

    sleep = parse_float(payload.get("sleep"))
    if sleep is None:
        sleep = parse_float(payload.get("sleep_score"))

    stress = parse_float(payload.get("stress"))
    if stress is None:
        stress = parse_float(payload.get("stress_score"))

    recovery = parse_float(payload.get("recovery"))
    if recovery is None:
        recovery = parse_float(payload.get("recovery_score"))

    pressure = payload.get("pressure")

    # Поддержка варианта systolic/diastolic
    if not pressure:
        systolic = parse_int(payload.get("systolic"))
        diastolic = parse_int(payload.get("diastolic"))
        if systolic is not None and diastolic is not None:
            pressure = f"{systolic}/{diastolic}"

    if sleep is None or stress is None or recovery is None:
        return jsonify({
            "ok": False,
            "error": "sleep, stress, recovery are required"
        }), 400

    biotime = compute_biotime(sleep, stress, recovery, pressure)

    data_store["biotime"] = biotime
    data_store["sleep"] = sleep
    data_store["stress"] = stress
    data_store["recovery"] = recovery
    data_store["pressure"] = pressure

    add_history_entry(
        biotime=biotime,
        sleep=sleep,
        stress=stress,
        recovery=recovery,
        pressure=pressure,
    )

    return jsonify({
        "ok": True,
        "data": {
            "biotime": biotime,
            "sleep": sleep,
            "stress": stress,
            "recovery": recovery,
            "pressure": pressure,
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

    seed_demo_history()
    refresh_dashboard_from_last_history()

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