from flask import request, jsonify
from bot.handler import handle_update

def register_routes(app):
    @app.get("/")
    def home():
        return "AION is alive 🚀", 200

    @app.post("/webhook")
    def webhook():
        update = request.get_json(silent=True) or {}
        try:
            handle_update(update)
        except Exception as e:
            print("WEBHOOK ERROR:", repr(e))
        return jsonify({"ok": True}), 200