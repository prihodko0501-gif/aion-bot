from flask import Blueprint, send_from_directory, jsonify
from pathlib import Path

# подключаем BioTime из ядра
from core.biotime import calculate_biotime

webapp = Blueprint(
    "webapp",
    __name__,
    static_folder="",
)

BASE_DIR = Path(__file__).resolve().parent


# -----------------------------
# Главная страница Mini App
# -----------------------------

@webapp.route("/")
def index():
    return send_from_directory(BASE_DIR, "index.html")


# -----------------------------
# CSS
# -----------------------------

@webapp.route("/aion.css")
def css():
    return send_from_directory(BASE_DIR, "aion.css")


# -----------------------------
# JS
# -----------------------------

@webapp.route("/aion.js")
def js():
    return send_from_directory(BASE_DIR, "aion.js")


# -----------------------------
# API BioTime
# -----------------------------

@webapp.route("/api/biotime")
def api_biotime():

    try:
        value = calculate_biotime()
    except:
        value = 0

    return jsonify({
        "value": value
    })


# -----------------------------
# Проверка сервера
# -----------------------------

@webapp.route("/api/status")
def status():

    return jsonify({
        "status": "ok",
        "system": "AION",
        "server": "running"
    })


# -----------------------------
# Modules page
# -----------------------------

@webapp.route("/modules")
def modules():
    return send_from_directory(BASE_DIR, "index.html")