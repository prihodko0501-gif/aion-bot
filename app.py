import os
from flask import Flask

from webapp.routes import register_routes
from database.core import init_db

app = Flask(__name__)

# Чтобы Flask не различал /webhook и /webhook/
app.url_map.strict_slashes = False

register_routes(app)
init_db()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", "8080"))
    app.run(host="0.0.0.0", port=port)