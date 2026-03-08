from flask import Flask, render_template_string

app = Flask(__name__)

@app.route("/")
def home():
    return "AION server running"

@app.route("/app")
def mini_app():
    html = """
    <html>
    <head>
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <style>
        body{
            margin:0;
            background:#0c0f1a;
            font-family:Arial;
            color:white;
            text-align:center;
        }
        img{
            width:100%;
            display:block;
        }
        .box{
            padding:20px;
        }
        p{
            font-size:20px;
            line-height:1.4;
        }
        </style>
    </head>
    <body>
        <img src="https://raw.githubusercontent.com/prihodko0501-gif/aion-bot/main/9C9D1C07-7426-4DDC-84DD-A76E6AC20138.png">
        <div class="box">
            <p>
            Система AION разработана как глобальная платформа,
            измеряющая биологическое время и помогающая управлять
            скоростью жизни
            </p>
        </div>
    </body>
    </html>
    """
    return render_template_string(html)

@app.route("/webhook", methods=["POST"])
def webhook():
    return "ok", 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)