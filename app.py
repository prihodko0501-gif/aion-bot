from flask import Flask, send_from_directory
from pathlib import Path

app = Flask(__name__)

BASE_DIR = Path(__file__).resolve().parent
WEBAPP_DIR = BASE_DIR / "webapp"
STATIC_DIR = WEBAPP_DIR / "static"


# Главная страница Mini App
@app.route("/")
def index():
    return send_from_directory(WEBAPP_DIR, "index.html")


# Статические файлы (иконки, css, js, png)
@app.route("/static/<path:path>")
def static_files(path):
    return send_from_directory(STATIC_DIR, path)


# Проверка работы сервера
@app.route("/health")
def health():
    return {"status": "ok"}


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)