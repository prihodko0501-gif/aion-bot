from flask import Flask, send_from_directory

app = Flask(__name__)

@app.get("/")
def home():
    return "AION is alive 🚀", 200

@app.get("/app")
def miniapp():
    return send_from_directory("webapp", "index.html")