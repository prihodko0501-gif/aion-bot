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

        <style>
            body{
                margin:0;
                background:#030814;
                overflow:hidden;
            }

            .screen{
                position:relative;
                width:100%;
                min-height:100vh;
                background:#030814;
            }

            .hero{
                width:100%;
                display:block;
            }

            .overlay{
                position:absolute;
                left:0;
                right:0;
                bottom:0;
                padding:42px 26px 70px 26px;
                background:linear-gradient(
                    to top,
                    rgba(3,8,20,0.96) 0%,
                    rgba(3,8,20,0.88) 35%,
                    rgba(3,8,20,0.45) 70%,
                    rgba(3,8,20,0.00) 100%
                );
                text-align:center;
            }

            .text{
                color:#f6c16d;
                font-size:32px;
                line-height:1.65;
                font-family:"Georgia", "Times New Roman", serif;
                font-style:italic;

                opacity:0;
                transform:translateY(20px);
                animation:fadeUp 2s ease forwards;
                animation-delay:0.35s;

                text-shadow:
                    0 0 6px rgba(246,193,109,0.45),
                    0 0 14px rgba(255,160,60,0.28),
                    0 0 26px rgba(255,140,40,0.16);
            }

            @keyframes fadeUp{
                from{
                    opacity:0;
                    transform:translateY(20px);
                }
                to{
                    opacity:1;
                    transform:translateY(0);
                }
            }

            @media (max-width: 480px){
                .overlay{
                    padding:34px 20px 54px 20px;
                }

                .text{
                    font-size:26px;
                    line-height:1.7;
                }
            }
        </style>
    </head>

    <body>
        <div class="screen">
            <img
                class="hero"
                src="https://raw.githubusercontent.com/prihodko0501-gif/aion-bot/main/563CC010-50CF-4E76-9C55-A3CEA18351D9.png"
                alt="AION"
            >

            <div class="overlay">
                <div class="text">
                    Система AION разработана<br>
                    как цифровая платформа,<br>
                    измеряющая биологическое время<br>
                    и помогающая управлять<br>
                    скоростью жизни
                </div>
            </div>
        </div>
    </body>
    </html>
    """


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "10000"))
    print(f"PORT={port}", flush=True)
    app.run(host="0.0.0.0", port=port)