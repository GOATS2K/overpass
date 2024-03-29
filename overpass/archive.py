from typing import Any, Dict, List
from flask.helpers import send_from_directory
from flask.wrappers import Response
from overpass.db import get_db, query_many
from flask import current_app
from os import environ
from pathlib import Path
from overpass.stream_utils import get_username_from_snowflake


def archive_stream(stream_key: str):
    """Archives a stream.

    Args:
        stream_key (str): The stream's stream key.
    """
    stream_path = Path(environ.get("REC_PATH", "")) / f"{stream_key}.mp4"
    current_app.logger.info(f"Adding stream {stream_path} to archive")
    db = get_db()
    db.execute(
        "UPDATE stream SET archived_file = ? WHERE stream_key = ?",
        (str(stream_path), stream_key),
    )
    db.commit()


def get_archived_streams(
    all_metadata: bool = False, private: bool = False
) -> List[Dict[str, Any]]:
    """Get a list of all archived streams.

    Args:
        all_metadata (bool, optional):
        Get all metadata for stream.
        Defaults to False.

        private (bool, optional):
        Include streams that aren't publically archived.
        Defaults to False.

    Returns:
        List[Dict[str, Any]]: List of dicts containing the streams.
    """
    if all_metadata:
        items = "*"
    else:
        items = "id, user_snowflake, start_date, end_date, title, description, category, unique_id"  # noqa: E501

    if private:
        res = query_many(
            f"SELECT {items} FROM stream WHERE archived_file IS NOT NULL"
        )
    else:
        res = query_many(
            f"SELECT {items} FROM stream WHERE unlisted = 0 AND archivable = 1 AND archived_file IS NOT NULL"  # noqa: E501
        )

    for stream in res:
        duration = stream["end_date"] - stream["start_date"]
        stream["duration"] = str(duration)
        stream["username"] = get_username_from_snowflake(
            stream["user_snowflake"]
        )
        stream["download"] = f"/archive/download/{stream['unique_id']}"
        if not private:
            del stream["user_snowflake"]

    return res


def serve_file(archived_stream: Dict[str, Any]) -> Response:
    """Serves an archived stream from storage.

    Args:
        archived_stream (Dict[str, Any]):
        Dict containing information about the stream from the database.

    Returns:
        Response: File being served by Flask's Response class.
    """
    username = get_username_from_snowflake(archived_stream["user_snowflake"])
    filename = f"{username} - {archived_stream['title']} - {archived_stream['start_date']}.mp4"
    return send_from_directory(
        environ.get("REC_PATH"),
        filename=f"{archived_stream['stream_key']}.mp4",
        as_attachment=True,
        attachment_filename=filename,
    )
