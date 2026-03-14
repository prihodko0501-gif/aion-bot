from flask import Flask, send_from_directory

app = Flask(__name__)

# главная страница Mini App
@app.route("/")
def index():
    return send_from_directory("webapp", "index.html")


# чтобы работали стили, иконки и скрипты
@app.route("/static/<path:path>")
def static_files(path):
    return send_from_directory("webapp/static", path)


# проверка сервера
@app.route("/health")
def health():
    return {"status": "ok"}


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)