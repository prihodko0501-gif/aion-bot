import os
from flask import Flask, request

app = Flask(__name__)


@app.route("/")
def home():
    return "AION Bot Running"


@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.json
    print(data)
    return {"status": "ok"}, 200


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "10000"))
    app.run(host="0.0.0.0", port=port)