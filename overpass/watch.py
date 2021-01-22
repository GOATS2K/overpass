from flask import Blueprint, render_template, redirect, url_for, request
from overpass.stream_utils import (
    get_livestreams_by_username,
    get_unlisted_livestreams_by_username,
)
from flask_discord import Unauthorized, requires_authorization
from overpass.archive import get_archived_streams
from overpass import discord

bp = Blueprint("watch", __name__)


@bp.errorhandler(Unauthorized)
def redirect_discord_unauthorized(e):
    return redirect(url_for("auth.login"))


@bp.before_request
@requires_authorization
def require_auth():
    pass


def get_archived_stream(unique_id, private=False):
    archived_streams = get_archived_streams(private=private)
    stream = next(
        stream for stream in archived_streams if stream["unique_id"] == unique_id
    )
    return stream


def return_stream_page(unique_id, stream):
    return render_template(
        "watch.html",
        id=unique_id,
        stream=stream,
        archive_link=stream["download"],
    )


@bp.route("/<username>")
@bp.route("/<username>/<unique_id>")
def watch_stream(username, unique_id=None):
    # ugh this function is so messy...
    stream = get_livestreams_by_username(username)
    if stream and not unique_id:
        # Regular livestream
        return render_template("watch.html", live=True, stream=stream)

    if unique_id:
        # Lets first check if its an unlisted stream
        unlisted = get_unlisted_livestreams_by_username(username)
        if unlisted:
            # Unlisted stream
            return render_template("watch.html", live=True, stream=unlisted)

        # It's an archived stream at this point
        try:
            stream = get_archived_stream(unique_id)
            return return_stream_page(unique_id, stream)
        except StopIteration:
            pass

        # Private stream
        try:
            user = discord.fetch_user()
            stream = get_archived_stream(unique_id, private=True)
            if stream["user_snowflake"] == user.id:
                return return_stream_page(unique_id, stream)
            else:
                return render_template("alert.html", error="Invalid stream key.")
        except StopIteration:
            # The stream ID doesn't exist at all at this point
            return (
                render_template("alert.html", error="Invalid stream key."),
                404,
            )

    return render_template("watch.html")
