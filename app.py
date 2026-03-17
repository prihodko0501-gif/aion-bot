from flask import Flask, send_from_directory, request, jsonify
from pathlib import Path
from datetime import datetime
import json

app = Flask(__name__)

BASE_DIR = Path(__file__).resolve().parent
WEBAPP_DIR = BASE_DIR / "webapp"
STATIC_DIR = WEBAPP_DIR / "static"
ICONS_DIR = STATIC_DIR / "icons"
DATA_FILE = BASE_DIR / "sleep_entries.json"


def load_entries():
    if not DATA_FILE.exists():
        return []
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []


def save_entries(entries):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(entries, f, ensure_ascii=False, indent=2)


def clamp(value, min_value, max_value):
    return max(min_value, min(value, max_value))


def calculate_sleep_score(hours, quality, fall_asleep, awakenings, morning):
    """
    Простая MVP-формула Sleep Score 0–100
    """
    # 1. Сон по часам
    if 7.5 <= hours <= 8.5:
        hours_score = 30
    elif 6.5 <= hours < 7.5 or 8.5 < hours <= 9.0:
        hours_score = 24
    elif 5.5 <= hours < 6.5 or 9.0 < hours <= 10.0:
        hours_score = 16
    else:
        hours_score = 8

    # 2. Качество сна: 1–10
    quality_score = clamp(quality, 1, 10) * 2.5  # max 25

    # 3. Засыпание: чем быстрее, тем лучше
    if fall_asleep <= 15:
        sleep_onset_score = 15
    elif fall_asleep <= 30:
        sleep_onset_score = 12
    elif fall_asleep <= 45:
        sleep_onset_score = 8
    else:
        sleep_onset_score = 4

    # 4. Пробуждения
    if awakenings == 0:
        awakenings_score = 15
    elif awakenings == 1:
        awakenings_score = 12
    elif awakenings == 2:
        awakenings_score = 8
    else:
        awakenings_score = 4

    # 5. Утреннее восстановление: 1–10
    morning_score = clamp(morning, 1, 10) * 1.5  # max 15

    total = round(hours_score + quality_score + sleep_onset_score + awakenings_score + morning_score)
    total = clamp(total, 0, 100)

    if total >= 85:
        status = "OPTIMAL"
        summary = "Сон сильный. Хорошее восстановление и высокий ресурс."
    elif total >= 70:
        status = "GOOD"
        summary = "Сон хороший. Есть база для нормального восстановления."
    elif total >= 50:
        status = "MODERATE"
        summary = "Сон средний. Есть точки для улучшения."
    else:
        status = "LOW"
        summary = "Сон слабый. Восстановление снижено, нужен пересмотр режима."

    return {
        "score": total,
        "status": status,
        "summary": summary
    }


@app.route("/")
def index():
    return send_from_directory(WEBAPP_DIR, "index.html")


@app.route("/health")
def health():
    return {"status": "ok"}


@app.route("/screen-1")
def screen_1():
    return send_from_directory(ICONS_DIR, "screen-1.webp.webp")


@app.route("/screen-2")
def screen_2():
    return send_from_directory(ICONS_DIR, "screen-2.webp.webp")


@app.route("/screen-3")
def screen_3():
    return send_from_directory(ICONS_DIR, "screen-3.webp.webp")


@app.route("/test-static")
def test_static():
    return send_from_directory(ICONS_DIR, "screen-1.webp.webp")


@app.route("/static/<path:path>")
def static_files(path):
    return send_from_directory(STATIC_DIR, path)


@app.route("/api/sleep", methods=["POST"])
def api_sleep():
    try:
        data = request.get_json(force=True) or {}

        hours = float(data.get("hours", 0))
        quality = int(data.get("quality", 0))
        fall_asleep = int(data.get("fall_asleep", 0))
        awakenings = int(data.get("awakenings", 0))
        morning = int(data.get("morning", 0))

        result = calculate_sleep_score(
            hours=hours,
            quality=quality,
            fall_asleep=fall_asleep,
            awakenings=awakenings,
            morning=morning,
        )

        entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "module": "sleep",
            "input": {
                "hours": hours,
                "quality": quality,
                "fall_asleep": fall_asleep,
                "awakenings": awakenings,
                "morning": morning,
            },
            "result": result,
        }

        entries = load_entries()
        entries.append(entry)
        save_entries(entries)

        return jsonify({
            "ok": True,
            "entry": entry
        })
    except Exception as e:
        return jsonify({
            "ok": False,
            "error": str(e)
        }), 400


@app.route("/api/sleep/latest", methods=["GET"])
def api_sleep_latest():
    entries = load_entries()
    sleep_entries = [x for x in entries if x.get("module") == "sleep"]

    if not sleep_entries:
        return jsonify({
            "ok": True,
            "entry": None
        })

    return jsonify({
        "ok": True,
        "entry": sleep_entries[-1]
    })


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)