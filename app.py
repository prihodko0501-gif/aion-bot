import os
from flask import Flask

app = Flask(__name__)

@app.route("/")
def home():
    return "AION BOT WORKING"

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    print("PORT =", port, flush=True)

    app.run(
        host="0.0.0.0",
        port=port,
        debug=False
    )