import uuid
from os import environ
from typing import Any

from flask import Blueprint, abort, redirect, request, url_for
from flask.templating import render_template
from flask_discord import Unauthorized, requires_authorization
from overpass import discord
from overpass.db import query_one
from overpass.forms import StreamGenerationForm
from overpass.stream_api import add_stream_to_db, update_db_fields

bp = Blueprint("stream", __name__)


@bp.errorhandler(Unauthorized)
def redirect_discord_unauthorized(e) -> Any:
    return redirect(url_for("auth.login"))


@bp.before_request
@requires_authorization
def require_auth() -> None:
    pass


@bp.route("/manage/<unique_id>", methods=["GET", "POST"])
def manage_stream(unique_id: str) -> Any:
    """Manage a stream's properties via its unique ID.

    Args:
        unique_id (str): The stream's unique ID.

    Returns:
        Any: A static page rendered by Flask.
    """
    user = discord.fetch_user()
    form = StreamGenerationForm()
    stream = query_one(
        """SELECT title,
        description,
        category,
        archivable,
        unlisted,
        user_snowflake
        FROM stream
        WHERE unique_id = ?
        """,
        [unique_id],
    )

    if not stream:
        return render_template("alert.html", error="Invalid stream ID."), 404

    # Populate the stream editing form.
    form.title.data = stream["title"]
    form.description.data = stream["description"]
    form.category.data = stream["category"]
    form.archivable.data = stream["archivable"]
    form.unlisted.data = stream["unlisted"]

    if stream["user_snowflake"] == user.id:
        if request.method == "GET":
            return render_template(
                "manage_stream.html", form=form, unique_id=unique_id
            )

        if request.method == "POST":
            form = StreamGenerationForm(request.form)
            if form.validate():
                keys_to_change = {}
                for key, value in form.data.items():
                    if stream[key] != value:
                        keys_to_change[key] = value
                update_db_fields(unique_id, **keys_to_change)
                return render_template(
                    "manage_stream.html",
                    form=form,
                    unique_id=unique_id,
                    update=True,
                )
    else:
        # User does not have access to manage this stream ID.
        return abort(403)


@bp.route("/generate", methods=["GET", "POST"])
def generate_stream_key() -> Any:
    form = StreamGenerationForm(request.form)
    server = f"rtmp://{environ.get('RTMP_SERVER')}"
    if request.method == "GET":
        return render_template(
            "generate_stream.html", form=form, server=server
        )
    else:
        user = discord.fetch_user()
        snowflake = user.id

        keyvar = uuid.uuid4()
        stream_key = str(keyvar)[0:8]
        unique_id = str(keyvar)[24:32]

        if form.validate():
            title = form.title.data
            description = form.description.data
            category = form.category.data
            archivable = form.archivable.data
            unlisted = form.unlisted.data

            add_stream_to_db(
                snowflake,
                title,
                description,
                category,
                archivable,
                unique_id,
                stream_key,
                unlisted,
            )

            return render_template(
                "generate_stream.html",
                form=form,
                user=user,
                key=stream_key,
                id=unique_id,
                unlisted=unlisted,
                server=server,
            )
