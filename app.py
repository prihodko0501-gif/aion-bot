from flask import Flask, render_template_string
import os

app = Flask(__name__)

IMAGE_URL = "https://raw.githubusercontent.com/prihodko0501-gif/aion-bot/main/9C9D1C07-7426-4DDC-84DD-A76E6AC20138.png"


@app.route("/")
def home():
    return "AION server running"


@app.route("/app")
def mini_app():
    html = f"""
    <html>
    <head>
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <style>
            body {{
                margin: 0;
                background: #050b18;
                color: white;
                text-align: center;
                font-family: Arial, sans-serif;
            }}

            .hero {{
                width: 100%;
            }}

            .hero img {{
                width: 100%;
                display: block;
            }}

            .text {{
                padding: 28px 22px 40px;
                font-size: 22px;
                line-height: 1.7;
                color: white;
            }}
        </style>
    </head>
    <body>

        <div class="hero">
            <img src="{IMAGE_URL}" alt="AION">
        </div>

        <div class="text">
            Система AION разработана как цифровая платформа,<br>
            измеряющая биологическое время<br>
            и помогающая управлять<br>
            скоростью жизни
        </div>

    </body>
    </html>
    """
    return render_template_string(html)


@app.route("/webhook", methods=["POST"])
def webhook():
    return "ok", 200


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)