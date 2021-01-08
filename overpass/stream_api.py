# flake8: noqa E501

from flask import request, Blueprint, redirect, url_for, current_app, jsonify
import uuid
from flask_discord import requires_authorization, Unauthorized
from overpass import discord
from overpass.db import get_db

# from overpass.app import app

bp = Blueprint("stream", __name__)


def add_stream_to_db(snowflake, title, description, category, stream_key):
    db = get_db()
    current_app.logger.info(
        f"Adding stream {title} by {snowflake} with stream key {stream_key} to database"
    )
    db.execute(
        "INSERT INTO stream (user_snowflake, title, description, category, stream_key) VALUES (?, ?, ?, ?, ?)",
        (snowflake, title, description, category, stream_key),
    )
    db.commit()


@bp.errorhandler(Unauthorized)
def redirect_discord_unauthorized(e):
    return redirect(url_for("auth.login"))


@bp.before_request
@requires_authorization
def require_auth():
    pass


@bp.route("/info")
def info() -> str:
    return "This doesn't do anything yet."


@bp.route("/generate", methods=["POST"])
def generate_stream_key():
    user = discord.fetch_user()
    snowflake = user.id

    req_json = request.get_json()
    title = req_json.get("title", "No title")
    description = req_json.get("description", "Unknown")
    category = req_json.get("category", "Unknown")

    stream_key = str(uuid.uuid1())[0:8]
    add_stream_to_db(snowflake, title, description, category, stream_key)

    return (
        jsonify({"message": "Stream key generation completed.", "key": stream_key}),
        200,
    )
