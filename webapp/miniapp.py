from flask import jsonify


def miniapp_status():
    """
    Проверка работы backend mini app
    """

    return jsonify({
        "status": "AION miniapp backend running"
    })
