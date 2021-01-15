from flask import Blueprint, request, current_app, jsonify
from overpass.db import query_db, get_db
from datetime import datetime
from overpass.stream_utils import get_unique_stream_id_from_stream_key
from overpass.archive import archive_stream

bp = Blueprint("rtmp", __name__)

# Accept only connections from localhost


def verify_stream_key(stream_key):
    res = query_db(
        "SELECT * from stream WHERE stream_key = ? AND end_date IS NULL",
        [stream_key],
        one=True,
    )
    try:
        if res["stream_key"]:
            current_app.logger.info(f"Accepting stream: {stream_key}")
            return True
    except TypeError:
        current_app.logger.info(f"Invalid stream key: {stream_key}")


def start_stream(stream_key):
    db = get_db()
    current_app.logger.info(f"Stream {stream_key} is now live!")
    res = query_db("SELECT * FROM stream WHERE stream_key = ?", [stream_key], one=True)
    db.execute(
        "UPDATE stream SET start_date = ? WHERE id = ?", (datetime.now(), res["id"])
    )
    db.commit()


def end_stream(stream_key):
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
        # Write stream start date to db
        start_stream(stream_key)
        unique_id = get_unique_stream_id_from_stream_key(stream_key)
        current_app.logger.info(f"This stream's unique ID is {unique_id}")
        return jsonify({"message": "Stream key is valid!"}), 200
    else:
        return jsonify({"message": "Incorrect stream key."}), 401


@bp.route("/done", methods=["POST"])
def done():
    stream_key = request.form["name"]
    # Write stream end date to db
    end_stream(stream_key)

    res = query_db("SELECT * FROM stream WHERE stream_key = ?", [stream_key], one=True)
    if bool(res["archivable"]):
        current_app.logger.info("Stream is archivable.")
        archive_stream(stream_key)
    else:
        current_app.logger.info("Stream is going to be archived privately.")
        archive_stream(stream_key, private=True)

    return jsonify({"message": "Stream has successfully ended"}), 200
