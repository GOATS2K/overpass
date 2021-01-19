from flask import Blueprint, render_template, redirect, url_for, request
from overpass.stream_utils import (
    get_livestreams_by_username,
    get_unlisted_livestreams_by_username,
)
from flask_discord import Unauthorized, requires_authorization
from overpass.archive import get_archived_streams

bp = Blueprint("watch", __name__)


@bp.errorhandler(Unauthorized)
def redirect_discord_unauthorized(e):
    return redirect(url_for("auth.login"))


@bp.before_request
@requires_authorization
def require_auth():
    pass


@bp.route("/<username>")
@bp.route("/<username>/<unique_id>")
def watch_stream(username, unique_id=None):
    stream = get_livestreams_by_username(username)
    if stream and not unique_id:
        return render_template("stream/watch.html", live=True, stream=stream)
    elif unique_id:
        # Lets first check if its an unlisted stream
        unlisted = get_unlisted_livestreams_by_username(username)
        if unlisted:
            return render_template("stream/watch.html", live=True, stream=unlisted)
        else:
            # It's an archived stream at this point
            archived_streams = get_archived_streams()
            try:
                stream = next(
                    stream
                    for stream in archived_streams
                    if stream["unique_id"] == unique_id
                )
                return render_template(
                    "stream/watch.html",
                    id=unique_id,
                    stream=stream,
                    archive_link=stream["download"],
                )
            except StopIteration:
                return render_template("alert.html", error="Invalid stream key.")
    else:
        return render_template("stream/watch.html")
