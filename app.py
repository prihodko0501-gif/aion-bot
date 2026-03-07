import os
from flask import Flask, request

app = Flask(__name__)

@app.route("/")
def home():
    return "AION BOT WORKING", 200

@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.get_json()
    print("TELEGRAM UPDATE:", data, flush=True)
    return "ok", 200

if __name__ == "__main__":
    port = int(os.environ.get("PORT", "10000"))
    print(f"PORT={port}", flush=True)
    app.run(host="0.0.0.0", port=port)