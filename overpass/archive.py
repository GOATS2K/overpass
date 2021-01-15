from flask import Blueprint, send_from_directory, jsonify, current_app
from overpass.db import query_db, get_db
from os import environ
from pathlib import Path
from overpass.stream_utils import get_username_from_snowflake

bp = Blueprint("archive", __name__)


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


@bp.route("/list")
def list_archived_streams():
    items = "id, user_snowflake, start_date, title, description, category, unique_id"
    res = query_db(
        f"SELECT {items} FROM stream WHERE unlisted = 0 AND archivable = 1 AND archived_file IS NOT NULL"
    )
    for stream in res:
        stream["username"] = get_username_from_snowflake(stream["user_snowflake"])
        stream["download"] = f"/archive/download/{stream['unique_id']}"
        del stream["user_snowflake"]

    return jsonify(res), 200


@bp.route("/download/<unique_id>")
def serve_archive(unique_id):
    res = query_db(
        "SELECT * FROM stream WHERE archivable = 1 AND unique_id = ?",
        [unique_id],
        one=True,
    )
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
    # Should render a 404 if the stream is unlisted
