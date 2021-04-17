from typing import Any, Dict
from overpass.db import query_one
from flask import current_app
from os import environ


def rewrite_stream_playlist(stream_key: str):
    """Re-write the stream's playlist file.
    This is run every time /hls/unique_id/index.m3u8 is requested.

    This is to ensure the stream key used doesn't get exposed
    to the users of the application.

    Args:
        stream_key (str): The stream's key.
    """
    path = environ.get("HLS_PATH", "")
    current_app.logger.info(f"Rewriting playlist for {stream_key}")
    with open(f"{path}/{stream_key}.m3u8", "r") as infile:
        lines = infile.readlines()

    with open(f"{path}/{stream_key}-index.m3u8", "w+") as outfile:
        outfile.seek(0)
        outfile.truncate()
        for line in lines:
            outfile.write(line.replace(f"{stream_key}-", ""))


def get_livestreams_by_username(username: str) -> Dict[str, Any]:
    """Get a user's current livestreams via their username.

    Args:
        username (str): The username you want to check for.

    Returns:
        Dict[str, Any]: The livestream's details.
    """
    items = "user_snowflake, start_date, title, description, category, unique_id"
    user_id = query_one("SELECT snowflake FROM user WHERE username = ?", [username])
    stream = query_one(
        f"SELECT {items} FROM stream WHERE user_snowflake = ? AND unlisted = 0 AND end_date IS NULL AND start_date IS NOT NULL",  # noqa: E501
        [user_id["snowflake"]],
    )
    if stream:
        stream["username"] = username
    return stream


def get_unlisted_livestreams_by_username(username: str) -> Dict[str, Any]:
    """Get a user's unlisted livestreams from their username.

    Args:
        username (str): The user's username.

    Returns:
        Dict[str, Any]: The unlisted livestream.
    """
    items = "user_snowflake, start_date, title, description, category, unique_id"
    res = query_one("SELECT snowflake FROM user WHERE username = ?", [username])
    stream = query_one(
        f"SELECT {items} FROM stream WHERE user_snowflake = ? AND unlisted = 1 AND end_date IS NULL AND start_date IS NOT NULL",  # noqa: E501
        [res["snowflake"]],
    )
    if stream:
        stream["username"] = username
    return stream


def get_username_from_snowflake(snowflake: int) -> str:
    """Get a user's username from a user ID.

    Args:
        snowflake (int): The user's ID.

    Returns:
        str: The user's username.
    """
    user = query_one("SELECT username FROM user WHERE snowflake = ?", [snowflake],)
    return user["username"]


def get_unique_stream_id_from_stream_key(stream_key: str) -> str:
    """Get a stream's unique ID from its key.

    Args:
        stream_key (str): The stream's key

    Returns:
        str: The unique ID.
    """
    res = query_one("SELECT unique_id FROM stream WHERE stream_key = ?", [stream_key])
    return res["unique_id"]


def get_stream_key_from_unique_id(unique_id: str) -> str:
    """Get a stream's stream key from its unique ID.

    Args:
        unique_id (str): The stream's unique ID.

    Returns:
        str: The stream key.
    """
    res = query_one("SELECT stream_key FROM stream WHERE unique_id = ?", [unique_id])
    return res["stream_key"]
