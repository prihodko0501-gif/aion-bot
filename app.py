from flask import Flask

app = Flask(__name__)

LOGO_URL = "https://raw.githubusercontent.com/prihodko0501-gif/aion-bot/main/B0AEE152-2F0A-4DD9-8A25-D25C1D6AFE54.jpeg"


@app.route("/")
def home():
    return "AION system online", 200


@app.route("/app")
def mini_app():
    return f"""
    <html>
    <head>
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
            html, body {{
                margin:0;
                padding:0;
                height:100%;
                background:#000;
                display:flex;
                justify-content:center;
                align-items:center;
            }}

            img {{
                width:90vw;
                max-width:600px;
            }}
        </style>
    </head>
    <body>
        <img src="{LOGO_URL}">
    </body>
    </html>
    """