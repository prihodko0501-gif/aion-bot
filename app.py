import os
from flask import Flask, request, jsonify

from bot.handler import handle_update

app = Flask(__name__)

@app.route("/", methods=["GET"])
def index():
    return "AION bot is running", 200

@app.route("/webhook", methods=["POST"])
def webhook():
    try:
        update = request.get_json(force=True, silent=True) or {}
        handle_update(update)
        return jsonify({"ok": True}), 200
    except Exception as e:
        print("WEBHOOK ERROR:", str(e))
        return jsonify({"ok": False, "error": str(e)}), 200  # webhook всегда 200

if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port)