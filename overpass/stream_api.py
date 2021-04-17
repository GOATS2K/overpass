# flake8: noqa E501

from typing import Any, Dict, List, Union, Text
from flask import (
    json,
    request,
    Blueprint,
    redirect,
    url_for,
    current_app,
    jsonify,
    abort,
)
import uuid
from flask.templating import render_template
from flask_discord import requires_authorization, Unauthorized
from overpass import discord
from overpass.db import get_db, query_many, query_one
from overpass.stream_utils import get_username_from_snowflake
from pathlib import Path
from os import environ
from overpass.forms import StreamGenerationForm

# from overpass.app import app

bp = Blueprint("stream", __name__)


@bp.errorhandler(Unauthorized)
def redirect_discord_unauthorized(e) -> Any:
    return redirect(url_for("auth.login"))


@bp.before_request
@requires_authorization
def require_auth() -> None:
    pass


def add_stream_to_db(
    snowflake: int,
    title: str,
    description: str,
    category: str,
    archivable: bool,
    unique_id: str,
    stream_key: str,
    unlisted: bool,
) -> None:
    """Adds the stream to the database.

    Args:
        snowflake (int): User ID of the user initiating the stream.
        title (str): Title of the stream.
        description (str): The stream's description.
        category (str): The stream's category.
        archivable (bool): Is the stream going to be publically archived?
        unique_id (str): The stream's unique ID.
        stream_key (str): The stream's stream key.
        unlisted (bool): Is the stream unlisted?
    """
    db = get_db()
    current_app.logger.info(
        f"Adding stream {title} by {snowflake} with stream key {stream_key} to database"
    )
    db.execute(
        "INSERT INTO stream (user_snowflake, title, description, category, archivable, unique_id, stream_key, unlisted) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        (
            snowflake,
            title,
            description,
            category,
            archivable,
            unique_id,
            stream_key,
            unlisted,
        ),
    )
    db.commit()


def verify_livestream(stream_key: str) -> bool:
    """Verifies that the stream's playlist exists on disk.

    Args:
        stream_key (str): The stream's key

    Returns:
        bool: True if the playlist exists, false if not.
    """
    stream_path = Path(environ.get("HLS_PATH", "")) / f"{stream_key}.m3u8"
    if stream_path.exists():
        return True
    else:
        return False


def get_current_livestreams() -> List[Dict[str, Any]]:
    """Gets all ongoing livestreams

    Returns:
        List[Dict[str, Any]]: A list of all ongoing livestreams in a dict.
    """
    items = "id, user_snowflake, start_date, title, description, category, stream_key, unique_id"
    res = query_many(
        f"SELECT {items} FROM stream WHERE start_date IS NOT NULL AND end_date IS NULL AND unlisted = 0"
    )
    for stream in res.copy():
        # It takes a while for nginx-rtmp to generate the HLS playlist
        # Therefore we won't show the stream until the file has been generated
        if not verify_livestream(stream["stream_key"]):
            res.remove(stream)

        stream["username"] = get_username_from_snowflake(stream["user_snowflake"])
        stream["hls"] = f"/hls/{stream['unique_id']}/index.m3u8"
        del stream["user_snowflake"]
        del stream["stream_key"]

    return res


def update_db_fields(unique_id: str, **kwargs) -> None:
    """Update the stream's properties in the database.

    Args:
        unique_id (str): The stream's unique ID.
    """
    db = get_db()
    for key, value in kwargs.items():
        current_app.logger.info(f"Updating field '{key}' in stream {unique_id}")
        db.execute(
            f"UPDATE stream SET {key} = ? WHERE unique_id = ?", (value, unique_id)
        )

    db.commit()


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
        "SELECT title, description, category, archivable, unlisted, user_snowflake FROM stream WHERE unique_id = ?",
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
            return render_template("manage_stream.html", form=form, unique_id=unique_id)

        if request.method == "POST":
            form = StreamGenerationForm(request.form)
            if form.validate():
                keys_to_change = {}
                for key, value in form.data.items():
                    if stream[key] != value:
                        keys_to_change[key] = value
                update_db_fields(unique_id, **keys_to_change)
                return render_template(
                    "manage_stream.html", form=form, unique_id=unique_id, update=True
                )
    else:
        # User does not have access to manage this stream ID.
        return abort(403)


@bp.route("/generate", methods=["GET", "POST"])
def generate_stream_key() -> Any:
    form = StreamGenerationForm(request.form)
    server = f"rtmp://{environ.get('RTMP_SERVER')}"
    if request.method == "GET":
        return render_template("generate_stream.html", form=form, server=server)
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
