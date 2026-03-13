from flask import request, jsonify
from bot.handler import handle_update
from webapp.miniapp import miniapp_bp, miniapp_home


def register_routes(app):
    # Подключаем Mini App
    app.register_blueprint(miniapp_bp)

    # Главная страница = Mini App
    @app.get("/")
    def home():
        return miniapp_home()

    # Webhook Telegram
    @app.post("/webhook")
    def webhook():
        update = request.get_json(silent=True)

        try:
            handle_update(update)
        except Exception as e:
            print("WEBHOOK ERROR:", repr(e))

        return jsonify({"ok": True}), 200

    # API Dashboard
    @app.get("/api/dashboard")
    def api_dashboard():
        return jsonify({
            "data": {
                "biotime": 8.4,
                "sleep": 92,
                "stress": 27,
                "recovery": 78,
                "pressure": "124/76",
                "date": "2026-03-13"
            }
        })

    # API History
    @app.get("/api/history")
    def api_history():
        return jsonify({
            "data": [
                {
                    "date": "2026-03-01",
                    "biotime": 7.8,
                    "sleep": 88,
                    "stress": 31,
                    "recovery": 74,
                    "pressure": "126/78"
                },
                {
                    "date": "2026-03-02",
                    "biotime": 8.0,
                    "sleep": 89,
                    "stress": 30,
                    "recovery": 75,
                    "pressure": "125/78"
                },
                {
                    "date": "2026-03-03",
                    "biotime": 8.2,
                    "sleep": 90,
                    "stress": 29,
                    "recovery": 76,
                    "pressure": "125/77"
                },
                {
                    "date": "2026-03-04",
                    "biotime": 8.3,
                    "sleep": 91,
                    "stress": 28,
                    "recovery": 76,
                    "pressure": "124/77"
                },
                {
                    "date": "2026-03-05",
                    "biotime": 8.1,
                    "sleep": 91,
                    "stress": 28,
                    "recovery": 77,
                    "pressure": "124/76"
                },
                {
                    "date": "2026-03-06",
                    "biotime": 8.4,
                    "sleep": 92,
                    "stress": 27,
                    "recovery": 78,
                    "pressure": "124/76"
                },
                {
                    "date": "2026-03-07",
                    "biotime": 8.5,
                    "sleep": 93,
                    "stress": 26,
                    "recovery": 79,
                    "pressure": "123/76"
                }
            ]
        })

    # API Sleep
    @app.get("/api/sleep")
    def api_sleep():
        return jsonify({
            "score": 92,
            "duration": "7h 25m",
            "latency": "5m",
            "stability": "94%"
        })

    # API Entry
    @app.post("/api/entry")
    def api_entry():
        payload = request.get_json(silent=True) or {}

        sleep = payload.get("sleep")
        stress = payload.get("stress")
        recovery = payload.get("recovery")
        systolic = payload.get("systolic")
        diastolic = payload.get("diastolic")

        pressure = None
        if systolic and diastolic:
            pressure = f"{systolic}/{diastolic}"

        # временный расчёт BioTime
        try:
            sleep_val = float(sleep or 0)
            stress_val = float(stress or 0)
            recovery_val = float(recovery or 0)

            biotime = round(((sleep_val / 10) * 1.2 + (recovery_val / 10) * 1.2 - (stress_val / 10)), 1)
            if biotime < 0:
                biotime = 0
            if biotime > 12:
                biotime = 12
        except Exception:
            return jsonify({
                "ok": False,
                "error": "invalid input"
            }), 400

        return jsonify({
            "ok": True,
            "data": {
                "biotime": biotime,
                "sleep": sleep,
                "stress": stress,
                "recovery": recovery,
                "pressure": pressure,
                "date": "2026-03-13"
            }
        })