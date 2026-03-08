from flask import Blueprint, send_from_directory

miniapp_bp = Blueprint("miniapp", __name__)

@miniapp_bp.get("/app")
def miniapp_home():
    return send_from_directory("webapp", "index.html")