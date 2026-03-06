from flask import Blueprint

miniapp_bp = Blueprint("miniapp", __name__)

@miniapp_bp.get("/miniapp")
def miniapp_home():
    return "<h1>AION MiniApp OK</h1><p>Стартовая страница MiniApp.</p>", 200