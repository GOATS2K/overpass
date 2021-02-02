from flask import (
    Blueprint,
    send_from_directory,
    current_app,
    redirect,
    url_for,
    request,
    abort,
)
from flask.templating import render_template
from overpass.db import query_db, get_db
from os import environ
from pathlib import Path
from overpass.stream_utils import get_username_from_snowflake
from flask_discord import Unauthorized, requires_authorization
from overpass import discord
from datetime import datetime


bp = Blueprint("archive", __name__)


@bp.errorhandler(Unauthorized)
def redirect_discord_unauthorized(e):
    return redirect(url_for("auth.login"))


@bp.before_request
@requires_authorization
def require_auth():
    pass


def archive_stream(stream_key, private=False):
    stream_path = Path(environ.get("REC_PATH")) / f"{stream_key}.mp4"
    current_app.logger.info(f"Adding stream {stream_path} to archive")
    db = get_db()
    db.execute(
        "UPDATE stream SET archived_file = ? WHERE stream_key = ?",
        (str(stream_path), stream_key),
    )
    if private:
        db.execute(
            "UPDATE stream SET archived_file = ? WHERE stream_key = ?",
            (str(stream_path), stream_key),
        )
    db.commit()


def get_archived_streams(all_metadata=False, private=False):
    if all_metadata:
        items = "*"
    else:
        items = "id, user_snowflake, start_date, end_date, title, description, category, unique_id"

    if private:
        res = query_db(f"SELECT {items} FROM stream WHERE archived_file IS NOT NULL")
    else:
        res = query_db(
            f"SELECT {items} FROM stream WHERE unlisted = 0 AND archivable = 1 AND archived_file IS NOT NULL"
        )

    for stream in res:
        duration = stream["end_date"] - stream["start_date"]
        stream["duration"] = str(duration)
        stream["username"] = get_username_from_snowflake(stream["user_snowflake"])
        stream["download"] = f"/archive/download/{stream['unique_id']}"
        if not private:
            del stream["user_snowflake"]

    return res


def serve_file(res):
    username = get_username_from_snowflake(res["user_snowflake"])
    filename = f"{username} - {res['title']} - {res['start_date']}.mp4"
    return send_from_directory(
        environ.get("REC_PATH"),
        filename=f"{res['stream_key']}.mp4",
        as_attachment=True,
        attachment_filename=filename,
    )


@bp.route("/")
def list_archived_streams():
    archive = get_archived_streams()
    if archive:
        return render_template("archive.html", archive=archive)
    else:
        return render_template("archive.html")


@bp.route("/download/<unique_id>")
def serve_archive(unique_id):
    user = discord.fetch_user()
    res = query_db(
        "SELECT * FROM stream WHERE archived_file IS NOT NULL AND unique_id = ?",
        [unique_id],
        one=True,
    )
    if user.id == res["user_snowflake"]:
        return serve_file(res)
    elif bool(res["archivable"]):
        return serve_file(res)
    else:
        return abort(404)
    # Should render a 404 if the stream is unlisted
