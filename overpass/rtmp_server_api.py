from flask import Blueprint, request, current_app, jsonify, abort
from overpass.db import get_db, query_one
from datetime import datetime
from overpass.stream_utils import get_unique_stream_id_from_stream_key
from overpass.archive import archive_stream
from typing import Any
import ipaddress

bp = Blueprint("rtmp", __name__)


@bp.before_request
def accept_only_private_ips() -> Any:
    """Make sure to only accept requests originating from
    the nginx-rtmp server, or an internal IP address.

    This is to ensure no one tampers with the streaming part
    of the application.

    Returns:
        Any: Returns a 401 if the request IP is invalid.
    """
    req_ip = ipaddress.IPv4Address(request.remote_addr)
    if not req_ip.is_private:
        return abort(401)


def verify_stream_key(stream_key: str) -> bool:
    """Validate that the stream key exists in the database

    Args:
        stream_key (str): The stream key to validate.

    Returns:
        bool: True if the key exists.
    """
    valid = False
    res = query_one(
        "SELECT * from stream WHERE stream_key = ? AND end_date IS NULL", [stream_key]
    )
    try:
        if res["stream_key"]:
            current_app.logger.info(f"Accepting stream: {stream_key}")
            valid = True
    except TypeError:
        current_app.logger.info(f"Invalid stream key: {stream_key}")

    return valid


def start_stream(stream_key: str) -> None:
    """Sets the stream's start date in the database.

    Args:
        stream_key (str): The stream key to update.
    """
    db = get_db()
    current_app.logger.info(f"Stream {stream_key} is now live!")
    res = query_one("SELECT * FROM stream WHERE stream_key = ?", [stream_key])
    db.execute(
        "UPDATE stream SET start_date = ? WHERE id = ?",
        (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), res["id"]),
    )
    db.commit()


def end_stream(stream_key: str) -> None:
    """Sets the stream's end date in the database.

    Args:
        stream_key (str): The stream key to update.
    """
    db = get_db()
    current_app.logger.info(f"Ending stream {stream_key}")
    res = query_one("SELECT * FROM stream WHERE stream_key = ?", [stream_key])
    db.execute(
        "UPDATE stream SET end_date = ? WHERE id = ?",
        (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), res["id"]),
    )
    db.commit()


@bp.route("/connect", methods=["POST"])
def connect() -> Any:
    """Accepts the initial connection request from nginx-rtmp
    If the stream key used is valid, accept the connection,
    else return 401.

    Returns:
        Any: 200 response if stream key is valid,
        401 response if stream key is invalid.
    """
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
def done() -> Any:
    """Mark the stream as done and archive the stream.

    Returns:
        Any: Returns 200 when the function has completed.
    """
    stream_key = request.form["name"]
    end_stream(stream_key)

    stream = query_one("SELECT * FROM stream WHERE stream_key = ?", [stream_key])
    if bool(stream["archivable"]):
        current_app.logger.info("Stream is archivable.")
    else:
        current_app.logger.info("Stream is going to be archived privately.")

    archive_stream(stream_key)
    return jsonify({"message": "Stream has successfully ended"}), 200
