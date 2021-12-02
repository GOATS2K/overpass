from typing import Any, Text

from flask import Blueprint, abort, redirect, url_for
from flask.templating import render_template
from flask.wrappers import Response
from flask_discord import Unauthorized, requires_authorization
from overpass import discord
from overpass.archive import get_archived_streams, serve_file
from overpass.db import query_one

bp = Blueprint("archive", __name__)


@bp.errorhandler(Unauthorized)
def redirect_discord_unauthorized(e) -> Any:
    return redirect(url_for("auth.login"))


@bp.before_request
@requires_authorization
def require_auth() -> None:
    pass


@bp.route("/")
def list_archived_streams() -> Text:
    """List publically archived streams.

    Returns:
        Text: Static page rendered by Flask.
    """
    archive = get_archived_streams()
    return render_template("archive.html", archive=archive)


@bp.route("/download/<unique_id>")
def serve_archive(unique_id: str) -> Response:
    """Serves stream from the archive.

    Args:
        unique_id (str): The stream's unique ID.

    Returns:
        Response: File being served by Flask's Response class.
    """
    user = discord.fetch_user()
    stream = query_one(
        """
        SELECT * FROM stream
        WHERE archived_file IS NOT NULL
        AND unique_id = ?
        """,
        [unique_id],
    )
    if user.id == stream["user_snowflake"]:
        # The user requesting the stream created it.
        # Therefore they shall always have access to the file.
        return serve_file(stream)
    elif bool(stream["archivable"]):
        # The stream is publically archived.
        return serve_file(stream)
    else:
        # The stream does not exist.
        return abort(404)
