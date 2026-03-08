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