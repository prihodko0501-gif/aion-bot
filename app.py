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
        <meta name="viewport" content="width=device-width, initial-scale=1, maximum-scale=1">
        <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
        <style>
            * {{
                box-sizing: border-box;
                -webkit-font-smoothing: antialiased;
                -moz-osx-font-smoothing: grayscale;
            }}

            body {{
                margin: 0;
                background: linear-gradient(180deg, #060b16 0%, #040814 100%);
                font-family: 'Inter', sans-serif;
                color: #ffffff;
                text-align: center;
            }}

            .wrap {{
                min-height: 100vh;
                display: flex;
                flex-direction: column;
            }}

            .hero {{
                width: 100%;
                display: block;
            }}

            .hero img {{
                width: 100%;
                height: auto;
                display: block;
            }}

            .text {{
                padding: 30px 24px 40px;
                font-size: 21px;
                line-height: 1.45;
                font-weight: 500;
                letter-spacing: 0.1px;
                color: rgba(255,255,255,0.96);
                text-wrap: balance;
            }}

            .text-inner {{
                max-width: 680px;
                margin: 0 auto;
            }}

            @media (max-width: 480px) {{
                .text {{
                    font-size: 19px;
                    padding: 26px 20px 34px;
                    line-height: 1.5;
                }}
            }}
        </style>
    </head>
    <body>
        <div class="wrap">
            <div class="hero">
                <img src="{IMAGE_URL}" alt="AION">
            </div>

            <div class="text">
                <div class="text-inner">
                    Система AION разработана как глобальная платформа,
                    измеряющая биологическое время и помогающая управлять
                    скоростью жизни
                </div>
            </div>
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