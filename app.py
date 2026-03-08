import os
from flask import Flask

app = Flask(__name__)

IMAGE_URL = "https://raw.githubusercontent.com/prihodko0501-gif/aion-bot/main/563CC010-50CF-4E76-9C55-A3CEA18351D9.png"


@app.route("/")
def home():
    return "AION BOT WORKING", 200


@app.route("/app")
def mini_app():
    return f"""
    <html>
    <head>
        <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
        <style>
            * {{
                box-sizing: border-box;
                -webkit-tap-highlight-color: transparent;
            }}

            html, body {{
                margin: 0;
                padding: 0;
                width: 100%;
                height: 100%;
                overflow: hidden;
                background: #020817;
                font-family: -apple-system, BlinkMacSystemFont, Arial, sans-serif;
            }}

            .screen {{
                position: relative;
                width: 100%;
                height: 100vh;
                overflow: hidden;
                background: #020817;
            }}

            .screen img {{
                width: 100%;
                height: 100%;
                object-fit: cover;
                display: block;
            }}

            .bottom-overlay {{
                position: absolute;
                left: 0;
                right: 0;
                bottom: 0;
                padding: 24px 18px 28px;
                background: linear-gradient(
                    to top,
                    rgba(2,8,23,0.95) 0%,
                    rgba(2,8,23,0.78) 35%,
                    rgba(2,8,23,0.35) 68%,
                    rgba(2,8,23,0.00) 100%
                );
            }}

            .open-btn {{
                width: 100%;
                border: 0;
                border-radius: 18px;
                padding: 17px 20px;
                font-size: 20px;
                font-weight: 600;
                color: white;
                cursor: pointer;
                background: linear-gradient(180deg, rgba(255,180,90,0.95), rgba(255,140,40,0.92));
                box-shadow:
                    0 8px 24px rgba(255,140,40,0.28),
                    0 0 18px rgba(255,190,110,0.22);
            }}

            .open-btn:active {{
                transform: scale(0.99);
            }}
        </style>
    </head>
    <body>
        <div class="screen">
            <img src="{IMAGE_URL}" alt="AION">

            <div class="bottom-overlay">
                <button class="open-btn" onclick="goNext()">Открыть</button>
            </div>
        </div>

        <script>
            function goNext() {{
                alert("Следующий экран AION подключим следующим шагом");
            }}
        </script>
    </body>
    </html>
    """


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "10000"))
    print(f"PORT={{port}}", flush=True)
    app.run(host="0.0.0.0", port=port)