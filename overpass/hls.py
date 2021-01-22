from flask import Blueprint, abort, send_from_directory, redirect, url_for
from overpass.stream_utils import rewrite_stream_playlist, get_stream_key_from_unique_id
from overpass.db import query_db
from os import environ
from flask_discord import Unauthorized, requires_authorization

bp = Blueprint("hls", __name__)


@bp.errorhandler(Unauthorized)
def redirect_discord_unauthorized(e):
    return redirect(url_for("auth.login"))


@bp.before_request
@requires_authorization
def require_auth():
    pass


@bp.after_request
def disable_cache(r):
    # https://stackoverflow.com/questions/31918035/javascript-only-works-after-opening-developer-tools-in-chrome
    # Finally fixed the HLS buffer issue...
    r.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    return r


@bp.route("/<unique_id>/<file>")
def serve_stream(unique_id, file):
    """
    Serve stream via unique ID

    Example:
    A stream uses the following IDs and keys:
    Stream key = 1451fgsa
    Unique ID = klzfls156

    When the user hits /watch/klzfls156/index.m3u8
    We give them HLS_DIR/1451fgsa.m3u8

    Now, when the user asks for files:
    /watch/klzfls156/1.ts
    We give them HLS_DIR/1451fgsa-1.ts
    """
    stream_key = get_stream_key_from_unique_id(unique_id)
    res = query_db(
        "SELECT end_date FROM stream WHERE stream_key = ?",
        [stream_key],
        one=True,
    )
    if stream_key and not res["end_date"]:
        if file == "index.m3u8":
            try:
                rewrite_stream_playlist(environ.get("HLS_PATH"), stream_key)
                return send_from_directory(
                    environ.get("HLS_PATH"), f"{stream_key}-index.m3u8"
                )
            except FileNotFoundError:
                return abort(404)
        else:
            return send_from_directory(environ.get("HLS_PATH"), f"{stream_key}-{file}")

    return abort(404)
