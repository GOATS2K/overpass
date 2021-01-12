from os import environ
from pathlib import Path
from flask import Blueprint, request, current_app, jsonify
from flask.helpers import make_response
from overpass.db import query_db, get_db
from datetime import datetime
from overpass.util import str_to_bool
from overpass.stream_utils import get_unique_stream_id_from_stream_key

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


def archive_stream(stream_key):
    stream_path = Path(environ.get("REC_PATH")) / f"{stream_key}.mp4"
    current_app.logger.info(f"Adding stream {stream_path} to archive")
    db = get_db()
    db.execute(
        "UPDATE stream SET archived_file = ? WHERE stream_key = ?",
        (str(stream_path), stream_key),
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
    if str_to_bool(res["archivable"]):
        current_app.logger.info("Stream is archivable.")
        archive_stream(stream_key)
    else:
        current_app.logger.info("Stream not going to be archived.")
    return jsonify({"message": "Stream has successfully ended"}), 200
