import os
from flask import Flask, request, jsonify
from bot.handler import handle_update

app = Flask(__name__)

@app.get("/")
def home():
    return "AION is alive 🚀", 200


@app.post("/webhook")
def webhook():
    update = request.get_json(silent=True) or {}
    handle_update(update)
    return jsonify({"ok": True})


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "8080"))
    app.run(host="0.0.0.0", port=port)