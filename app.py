import os
from flask import Flask

app = Flask(__name__)


@app.route("/")
def home():
    return "AION BOT WORKING", 200


@app.route("/app")
def mini_app():
    return """
    <html>
    <head>
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
    </head>

    <body style="margin:0;background:black;">

        <img src="https://raw.githubusercontent.com/prihodko0501-gif/aion-bot/main/563CC010-50CF-4E76-9C55-A3CEA18351D9.png"
        style="width:100%;display:block;">

    </body>
    </html>
    """


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "10000"))
    print(f"PORT={port}", flush=True)
    app.run(host="0.0.0.0", port=port)