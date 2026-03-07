from flask import Flask, request, render_template_string
import os

app = Flask(__name__)

@app.route("/")
def index():
    return "AION server working"

@app.route("/app")
def mini_app():

    html = """
    <html>
    <head>
    <meta name="viewport" content="width=device-width, initial-scale=1">

    <style>

    body{
        margin:0;
        font-family:Arial;
        background:#0c0f1a;
        color:white;
        text-align:center;
    }

    .card{
        max-width:500px;
        margin:auto;
        padding:20px;
    }

    img{
        width:100%;
        border-radius:16px;
        margin-top:20px;
    }

    h1{
        font-size:28px;
        margin-top:25px;
    }

    p{
        font-size:18px;
        line-height:1.5;
        opacity:0.9;
    }

    .btn{
        margin-top:30px;
        padding:18px;
        font-size:20px;
        background:#2b6cff;
        border-radius:12px;
        text-decoration:none;
        color:white;
        display:block;
    }

    </style>
    </head>

    <body>

    <div class="card">

    <img src="https://raw.githubusercontent.com/prihodko0501-gif/aion-bot/refs/heads/main/9C9D1C07-7426-4DDC-84DD-A76E6AC20138.png">

    <h1>AION</h1>

    <p>
    Система AION разработана как глобальная платформа,
    измеряющая биологическое время и помогающая управлять
    скоростью жизни
    </p>

    <a class="btn" href="#">
    Начать расчет
    </a>

    </div>

    </body>
    </html>
    """

    return render_template_string(html)


@app.route("/webhook", methods=["POST"])
def telegram_webhook():
    return "ok"


if __name__ == "__main__":
    app.run()