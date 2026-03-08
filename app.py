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
        <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
        <style>
            html, body {{
                margin: 0;
                padding: 0;
                width: 100%;
                height: 100%;
                background: #000;
                overflow: hidden;
            }}

            .screen {{
                width: 100%;
                height: 100vh;
                display: flex;
                align-items: center;
                justify-content: center;
                background: #000;
            }}

            .logo {{
                width: 88vw;
                max-width: 520px;
                display: block;
            }}
        </style>
    </head>
    <body>
        <div class="screen">
            <img class="logo" src="{LOGO_URL}" alt="AION">
        </div>
    </body>
    </html>
    """