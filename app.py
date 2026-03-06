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