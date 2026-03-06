from flask import jsonify


def register_routes(app):

    @app.get("/")
    def home():
        return "AION backend running", 200

    @app.get("/miniapp")
    def miniapp():
        return """
        <html>
          <head><title>AION Mini App</title></head>
          <body style="font-family: Arial; padding: 24px;">
            <h1>AION Mini App</h1>
            <p>Mini App backend is alive.</p>
          </body>
        </html>
        """, 200