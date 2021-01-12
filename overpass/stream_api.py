# flake8: noqa E501

from flask import json, request, Blueprint, redirect, url_for, current_app, jsonify
import uuid
from flask_discord import requires_authorization, Unauthorized
from overpass import discord
from overpass.db import get_db, query_db
from overpass.stream_utils import get_stream_key_from_unique_id, rewrite_stream_playlist
from pathlib import Path
from os import environ
from flask.helpers import send_from_directory

# from overpass.app import app

bp = Blueprint("stream", __name__)


def add_stream_to_db(
    snowflake, title, description, category, archivable, unique_id, stream_key
):
    db = get_db()
    current_app.logger.info(
        f"Adding stream {title} by {snowflake} with stream key {stream_key} to database"
    )
    db.execute(
        "INSERT INTO stream (user_snowflake, title, description, category, archivable, unique_id, stream_key) VALUES (?, ?, ?, ?, ?, ?, ?)",
        (snowflake, title, description, category, archivable, unique_id, stream_key),
    )
    db.commit()


def get_current_livestreams():
    items = "id, user_snowflake, start_date, title, description, category, unique_id"
    res = query_db(f"SELECT {items} FROM stream WHERE end_date IS NULL")
    for stream in res:
        user = query_db(
            "SELECT username FROM user WHERE snowflake = ?",
            [stream["user_snowflake"]],
            one=True,
        )
        stream["username"] = user["username"]
        stream["hls"] = f"/api/stream/watch/{stream['unique_id']}/index.m3u8"
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


@bp.route("/watch/<unique_id>/<file>")
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
    # This will probably be re-written in NGINX in the end
    stream_key = get_stream_key_from_unique_id(unique_id)
    res = query_db(
        "SELECT end_date FROM stream WHERE stream_key = ?", [stream_key], one=True
    )
    if stream_key and not res["end_date"]:
        if file == "index.m3u8":
            rewrite_stream_playlist(environ.get("HLS_PATH"), stream_key)
            return send_from_directory(
                environ.get("HLS_PATH"), f"{stream_key}-index.m3u8"
            )
        else:
            return send_from_directory(environ.get("HLS_PATH"), f"{stream_key}-{file}")
    else:
        return (
            jsonify({"message": "Invalid stream ID or the stream has just ended."}),
            404,
        )


@bp.route("/archive/download/<unique_id>")
def serve_archive(unique_id):
    res = query_db("SELECT * FROM stream WHERE unique_id = ?", [unique_id], one=True)
    if res["archived_file"]:
        user = query_db(
            "SELECT username FROM user WHERE snowflake = ?",
            [res["user_snowflake"]],
            one=True,
        )
        filename = f"{user['username']} - {res['title']} - {res['start_date']}.mp4"
        return send_from_directory(
            environ.get("REC_PATH"),
            filename=f"{res['stream_key']}.mp4",
            as_attachment=True,
            attachment_filename=filename,
        )


@bp.route("/archive/list")
def list_archived_streams():
    items = "id, user_snowflake, start_date, title, description, category, unique_id"
    res = query_db(f"SELECT {items} FROM stream WHERE archived_file IS NOT NULL")
    for stream in res:
        stream["download"] = f"/api/stream/archive/download/{stream['unique_id']}"

    return jsonify(res), 200


@bp.route("/generate", methods=["POST"])
def generate_stream_key():
    user = discord.fetch_user()
    snowflake = user.id

    req_json = request.get_json()
    title = req_json.get("title", "No title")
    description = req_json.get("description", "Unknown")
    category = req_json.get("category", "Unknown")
    archivable = req_json.get("archivable", False)

    keyvar = uuid.uuid4()
    stream_key = str(keyvar)[0:8]
    unique_id = str(keyvar)[24:32]
    add_stream_to_db(
        snowflake, title, description, category, archivable, unique_id, stream_key
    )

    return (
        jsonify({"message": "Stream key generation completed.", "key": stream_key}),
        200,
    )
