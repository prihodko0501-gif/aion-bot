import os
from flask import Flask

print("APP.PY STARTED")

from webapp.routes import register_routes

print("ROUTES IMPORTED")

app = Flask(__name__)
app.url_map.strict_slashes = False

register_routes(app)

print("ROUTES REGISTERED")

if __name__ == "__main__":
    port = int(os.environ.get("PORT", "8080"))
    print("RUNNING ON PORT", port)
    app.run(host="0.0.0.0", port=port)