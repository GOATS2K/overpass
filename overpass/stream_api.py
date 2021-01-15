# flake8: noqa E501

from flask import json, request, Blueprint, redirect, url_for, current_app, jsonify
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


def get_current_livestreams():
    items = "id, user_snowflake, start_date, title, description, category, unique_id"
    res = query_db(
        f"SELECT {items} FROM stream WHERE start_date IS NOT NULL AND end_date IS NULL AND unlisted = 0"
    )
    for stream in res:
        stream["username"] = get_username_from_snowflake(stream["user_snowflake"])
        stream["hls"] = f"/hls/{stream['unique_id']}/index.m3u8"
        del stream["user_snowflake"]

    return res


@bp.errorhandler(Unauthorized)
def redirect_discord_unauthorized(e):
    return redirect(url_for("auth.login"))


@bp.before_request
@requires_authorization
def require_auth():
    pass


@bp.route("/livestreams")
def livestreams():
    return jsonify(get_current_livestreams()), 200


@bp.route("/generate", methods=["GET", "POST"])
def generate_stream_key():
    form = StreamGenerationForm(request.form)
    if request.method == "GET":
        return render_template("stream/generate.html", form=form)
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
                "stream/generate.html", form=form, key=stream_key, id=unique_id
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
