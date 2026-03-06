import os
from flask import Flask

from webapp.routes import register_routes
from database.core import init_db

# AION engine
from core.biotime import calculate_aion_state

app = Flask(__name__)

# Чтобы Flask не различал /webhook и /webhook/
app.url_map.strict_slashes = False

# регистрация роутов
register_routes(app)

# инициализация базы
init_db()


@app.route("/")
def health():
    return {
        "status": "AION online",
        "engine": "biological upgrade system"
    }


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "8080"))
    app.run(host="0.0.0.0", port=port)