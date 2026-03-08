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

        <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&display=swap" rel="stylesheet">

        <style>

        body {{
            margin:0;
            background:linear-gradient(180deg,#060b16,#040814);
            font-family:'Inter',sans-serif;
            color:white;
            text-align:center;
        }}

        .hero img {{
            width:100%;
            display:block;
        }}

        .text {{
            padding:36px 28px;
            font-size:22px;
            line-height:1.7;
            opacity:0;
            animation:fadeIn 1.8s ease forwards;
            animation-delay:0.6s;

            text-shadow:
                0 0 10px rgba(255,255,255,0.15),
                0 0 20px rgba(120,180,255,0.10);
        }}

        @keyframes fadeIn {{
            from {{
                opacity:0;
                transform:translateY(15px);
            }}
            to {{
                opacity:1;
                transform:translateY(0);
            }}
        }}

        </style>

    </head>

    <body>

        <div class="hero">
            <img src="{IMAGE_URL}">
        </div>

        <div class="text">
        Система AION разработана как глобальная платформа,<br><br>
        измеряющая биологическое время<br><br>
        и помогающая управлять скоростью жизни
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