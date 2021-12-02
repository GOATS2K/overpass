from datetime import datetime

from flask import current_app

from overpass.db import get_db, query_one


def verify_stream_key(stream_key: str) -> bool:
    """Validate that the stream key exists in the database

    Args:
        stream_key (str): The stream key to validate.

    Returns:
        bool: True if the key exists.
    """
    res = query_one(
        "SELECT * from stream WHERE stream_key = ? AND end_date IS NULL",
        [stream_key],
    )
    try:
        if res["stream_key"]:
            current_app.logger.info(f"Accepting stream: {stream_key}")
            return True
    except KeyError:
        current_app.logger.info(f"Invalid stream key: {stream_key}")

    return False


def start_stream(stream_key: str) -> None:
    """Sets the stream's start date in the database.

    Args:
        stream_key (str): The stream key to update.
    """
    db = get_db()
    current_app.logger.info(f"Stream {stream_key} is now live!")
    res = query_one("SELECT * FROM stream WHERE stream_key = ?", [stream_key])
    db.execute(
        "UPDATE stream SET start_date = ? WHERE id = ?",
        (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), res["id"]),
    )
    db.commit()


def end_stream(stream_key: str) -> None:
    """Sets the stream's end date in the database.

    Args:
        stream_key (str): The stream key to update.
    """
    db = get_db()
    current_app.logger.info(f"Ending stream {stream_key}")
    res = query_one("SELECT * FROM stream WHERE stream_key = ?", [stream_key])
    db.execute(
        "UPDATE stream SET end_date = ? WHERE id = ?",
        (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), res["id"]),
    )
    db.commit()
