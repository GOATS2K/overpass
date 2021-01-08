from flask import Blueprint, request, current_app, jsonify
from overpass.db import query_db, get_db
from datetime import datetime

bp = Blueprint("rtmp", __name__)

# Accept only connections from localhost


def verify_stream_key(stream_key):
    res = query_db(
        "SELECT * from stream WHERE stream_key = ? AND end_date IS NULL",
        [stream_key],
        one=True,
    )
    try:
        if res["stream_key"] == stream_key:
            current_app.logger.info(f"Accepting stream: {stream_key}")
            return True
    except TypeError:
        current_app.logger.info(f"Invalid stream key: {stream_key}")


def end_stream(stream_key, **kwargs):
    db = get_db()
    current_app.logger.info(f"Ending stream {stream_key}")
    res = query_db("SELECT * FROM stream WHERE stream_key = ?", [stream_key], one=True)
    db.execute(
        "UPDATE stream SET end_date = ? WHERE id = ?", (datetime.now(), res["id"])
    )
    db.commit()


@bp.route("/connect", methods=["POST"])
def connect():
    stream_key = request.form["name"]
    if verify_stream_key(stream_key):
        return jsonify({"message": "Access granted!"}), 200
    else:
        return jsonify({"message": "Incorrect stream key."}), 401


@bp.route("/done", methods=["POST"])
def done():
    stream_key = request.form["name"]
    end_stream(stream_key)
    return jsonify({"message": "Stream has successfully ended"}), 200
