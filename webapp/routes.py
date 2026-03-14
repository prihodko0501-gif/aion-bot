from flask import jsonify
from core.biotime import calculate_biotime

@app.route("/api/biotime")
def api_biotime():

    value = calculate_biotime()

    return jsonify({
        "value": value
    })