from flask import request, jsonify
from bot.handler import handle_update


def register_routes(app):

    @app.route("/")
    def home():
        return "AION server running"

    @app.route("/webhook", methods=["POST"])
    def webhook():

        data = request.json

        if data:
            handle_update(data)

        return jsonify({"status": "ok"})
