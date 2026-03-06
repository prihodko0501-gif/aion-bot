import os
from flask import Flask, request, jsonify
from bot.handler import handle_update

app = Flask(__name__)


@app.get("/")
def home():
    return "AION bot is running", 200


@app.post("/webhook")
def webhook():
    try:
        update = request.get_json(silent=True) or {}
        print("UPDATE:", update)
        handle_update(update)
        return jsonify({"ok": True}), 200
    except Exception as e:
        print("WEBHOOK ERROR:", e)
        return jsonify({"ok": False, "error": str(e)}), 200


if __name__ == "__main__":
    port = int(os.getenv("PORT", "10000"))
    app.run(host="0.0.0.0", port=port)