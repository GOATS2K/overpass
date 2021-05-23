from typing import Any, Union

from flask import Blueprint, redirect, render_template, url_for
from flask_discord import Unauthorized, requires_authorization
from overpass import discord
from overpass.stream_utils import (
    get_livestreams_by_username,
    get_unlisted_livestreams_by_username,
)
from overpass.watch import get_single_archived_stream, return_stream_page

bp = Blueprint("watch", __name__)


@bp.errorhandler(Unauthorized)
def redirect_discord_unauthorized(e) -> Any:
    return redirect(url_for("auth.login"))


@bp.before_request
@requires_authorization
def require_auth() -> None:
    pass


@bp.route("/<username>")
@bp.route("/<username>/<unique_id>")
def watch_stream(username: str, unique_id: Union[str, None] = None) -> Any:
    """Generates a page to watch streams with.

    Args:
        username (str): The user whose stream to watch
        unique_id (Union[str, None], optional): The unique ID of a stream.
        This is only set if the stream is either private, or archived.
        Defaults to None.

    Returns:
        Any: Static page rendered by Flask.
    """
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
            stream = get_single_archived_stream(unique_id)
            return return_stream_page(unique_id, stream)
        except StopIteration:
            pass

        # Unlisted and archived
        try:
            stream = get_single_archived_stream(
                unique_id, all_metadata=True, private=True
            )
            if bool(stream["archivable"]) and bool(stream["unlisted"]):
                return return_stream_page(unique_id, stream)
        except StopIteration:
            pass

        # Private stream
        try:
            user = discord.fetch_user()
            stream = get_single_archived_stream(unique_id, private=True)
            if stream["user_snowflake"] == user.id:
                return return_stream_page(unique_id, stream)
            else:
                return render_template(
                    "alert.html", error="Invalid stream key."
                )
        except StopIteration:
            # The stream ID doesn't exist at all at this point
            return (
                render_template("alert.html", error="Invalid stream key."),
                404,
            )

    return render_template("watch.html")
