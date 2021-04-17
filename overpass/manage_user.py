from typing import Text
from flask import Blueprint, redirect, url_for
from flask.templating import render_template
from flask_discord import Unauthorized, requires_authorization
from overpass.db import query_many, query_one
from overpass import discord

bp = Blueprint("manage", __name__)


@bp.errorhandler(Unauthorized)
def redirect_discord_unauthorized(e):
    return redirect(url_for("auth.login"))


@bp.before_request
@requires_authorization
def require_auth():
    pass


@bp.route("/me")
def me() -> Text:
    """Render a page to manage stream properties

    Returns:
        Text: Static page rendered by Flask.
    """
    discord_user = discord.fetch_user()
    user = query_one("SELECT * FROM user WHERE snowflake = ?", [discord_user.id])
    streams = query_many(
        "SELECT * FROM stream WHERE user_snowflake = ?", [discord_user.id]
    )
    if streams:
        for stream in streams:
            try:
                duration = stream["end_date"] - stream["start_date"]
                stream["duration"] = str(duration)
            except TypeError:
                continue
            stream["username"] = user["username"]
        return render_template("manage_user.html", user=user, streams=streams)

    return render_template("manage_user.html", user=user)
