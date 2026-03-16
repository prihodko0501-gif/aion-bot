from flask import Flask, send_from_directory
from pathlib import Path

app = Flask(__name__)

BASE_DIR = Path(__file__).resolve().parent
WEBAPP_DIR = BASE_DIR / "webapp"
STATIC_DIR = WEBAPP_DIR / "static"
ICONS_DIR = STATIC_DIR / "icons"


@app.route("/")
def index():
    return send_from_directory(WEBAPP_DIR, "index.html")


@app.route("/health")
def health():
    return {"status": "ok"}


@app.route("/screen-1")
def screen_1():
    return send_from_directory(ICONS_DIR, "screen-1.webp.webp")


@app.route("/screen-2")
def screen_2():
    return send_from_directory(ICONS_DIR, "screen-2.webp.webp")


@app.route("/screen-3")
def screen_3():
    return send_from_directory(ICONS_DIR, "screen-3.webp.webp")


@app.route("/test-static")
def test_static():
    return send_from_directory(ICONS_DIR, "screen-1.webp.webp")


@app.route("/static/<path:path>")
def static_files(path):
    return send_from_directory(STATIC_DIR, path)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)