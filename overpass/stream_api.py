# flake8: noqa E501

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
from overpass.db import get_db, query_db
from overpass.stream_utils import (
    get_stream_key_from_unique_id,
    rewrite_stream_playlist,
    get_username_from_snowflake,
)
from pathlib import Path
from os import environ
from flask.helpers import send_from_directory
from overpass.forms import StreamGenerationForm

# from overpass.app import app

bp = Blueprint("stream", __name__)


def add_stream_to_db(
    snowflake, title, description, category, archivable, unique_id, stream_key, unlisted
):
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


def verify_livestream(stream_key):
    stream_path = Path(environ.get("HLS_PATH")) / f"{stream_key}.m3u8"
    if stream_path.exists():
        return True


def get_current_livestreams():
    items = "id, user_snowflake, start_date, title, description, category, stream_key, unique_id"
    res = query_db(
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


@bp.errorhandler(Unauthorized)
def redirect_discord_unauthorized(e):
    return redirect(url_for("auth.login"))


@bp.before_request
@requires_authorization
def require_auth():
    pass


def update_db_fields(unique_id, **kwargs):
    db = get_db()
    for key, value in kwargs.items():
        current_app.logger.info(f"Updating field '{key}' in stream {unique_id}")
        db.execute(
            f"UPDATE stream SET {key} = ? WHERE unique_id = ?", (value, unique_id)
        )

    db.commit()


@bp.route("/manage/<unique_id>", methods=["GET", "POST"])
def manage_stream(unique_id):
    user = discord.fetch_user()
    form = StreamGenerationForm()
    stream = query_db(
        "SELECT title, description, category, archivable, unlisted, user_snowflake FROM stream WHERE unique_id = ?",
        [unique_id],
        one=True,
    )

    if not stream:
        return render_template("alert.html", error="Invalid stream ID."), 404

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
def generate_stream_key():
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

            return_str = render_template(
                "generate_stream.html",
                form=form,
                user=user,
                key=stream_key,
                id=unique_id,
                unlisted=unlisted,
                server=server,
            )
        else:
            req_json = request.get_json()
            title = req_json.get("title", "No title")
            description = req_json.get("description", "Unknown")
            category = req_json.get("category", "Unknown")
            archivable = req_json.get("archivable", False)
            unlisted = req_json.get("unlisted", False)

            return_str = (
                jsonify(
                    {
                        "message": "Stream key generation completed.",
                        "key": stream_key,
                        "unique_id": unique_id,
                    }
                ),
            )
            200

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

        return return_str
