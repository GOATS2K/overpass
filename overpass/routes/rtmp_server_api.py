import ipaddress
from typing import Any

from flask import Blueprint, abort, current_app, jsonify, request
from overpass.archive import archive_stream
from overpass.db import query_one
from overpass.rtmp_server_api import (
    end_stream,
    start_stream,
    verify_stream_key,
)
from overpass.stream_utils import get_unique_stream_id_from_stream_key

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

    stream = query_one(
        "SELECT * FROM stream WHERE stream_key = ?", [stream_key]
    )
    if bool(stream["archivable"]):
        current_app.logger.info("Stream is archivable.")
    else:
        current_app.logger.info("Stream is going to be archived privately.")

    archive_stream(stream_key)
    return jsonify({"message": "Stream has successfully ended"}), 200
