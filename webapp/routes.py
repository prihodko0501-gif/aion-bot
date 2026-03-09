from flask import request, jsonify
from bot.handler import handle_update
from webapp.miniapp import miniapp_bp


def register_routes(app):

    # Подключаем Mini App
    app.register_blueprint(miniapp_bp)


    # Главная страница
    @app.get("/")
    def home():
        return "AION is alive 🚀", 200


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
        return {
            "biotime": 8.4,
            "sleep": 92,
            "stress": 27,
            "recovery": 78,
            "pressure": "124/76"
        }


    # API History
    @app.get("/api/history")
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


    # API Sleep
    @app.get("/api/sleep")
    def api_sleep():
        return {
            "score": 92,
            "duration": "7h 25m",
            "latency": "5m",
            "stability": "94%"
        }