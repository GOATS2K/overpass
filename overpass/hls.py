from typing import Any
from flask import Blueprint, abort, send_from_directory, redirect, url_for
from requests.sessions import Request
from overpass.stream_utils import rewrite_stream_playlist, get_stream_key_from_unique_id
from overpass.db import query_one
from os import environ
from flask_discord import Unauthorized, requires_authorization

bp = Blueprint("hls", __name__)


@bp.errorhandler(Unauthorized)
def redirect_discord_unauthorized(e):
    return redirect(url_for("auth.login"))


@bp.before_request
@requires_authorization
def require_auth() -> None:
    pass


@bp.after_request
def disable_cache(r: Request):
    # https://stackoverflow.com/questions/31918035/javascript-only-works-after-opening-developer-tools-in-chrome
    # Finally fixed the HLS buffer issue...
    r.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    return r


@bp.route("/<unique_id>/<file>")
def serve_stream(unique_id: str, file: str) -> Any:
    """Serve stream via its unique ID

    Example:
    A stream uses the following IDs and keys:
    Stream key = 1451fgsa
    Unique ID = klzfls156

    GET /watch/klzfls156/index.m3u8
    < HLS_DIR/1451fgsa-index.m3u8

    GET /watch/klzfls156/1.ts
    < HLS_DIR/1451fgsa-1.ts

    Args:
        unique_id (str): The stream's unique ID
        file (str): The requested file

    Returns:
        Any: Serves file from HLS path if exists.
    """
    stream_key = get_stream_key_from_unique_id(unique_id)
    stream = query_one("SELECT end_date FROM stream WHERE stream_key = ?", [stream_key])
    if stream_key and not stream["end_date"]:
        if file == "index.m3u8":
            try:
                rewrite_stream_playlist(stream_key)
                return send_from_directory(
                    environ.get("HLS_PATH"), f"{stream_key}-index.m3u8"
                )
            except FileNotFoundError:
                return abort(404)
        else:
            return send_from_directory(environ.get("HLS_PATH"), f"{stream_key}-{file}")

    return abort(404)
