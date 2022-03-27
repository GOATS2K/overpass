# flake8: noqa E501
# from flask import current_app as app
from typing import Union

from flask.globals import current_app
from pydantic import parse_obj_as
from overpass import discord
from datetime import datetime
from overpass.db import get_db
import os

from overpass.models import User

DISCORD_GUILD_ID = os.environ.get("DISCORD_GUILD_ID") or ""


def verify() -> bool:
    """Verifies if user exists in the Discord guild

    Returns:
        bool: User exists in guild
    """
    guilds = discord.fetch_guilds()
    return bool(
        next((i for i in guilds if i.id == int(DISCORD_GUILD_ID)), False)
    )


def add_user(username: str, snowflake: int, avatar: Union[str, None]) -> None:
    """Adds user to database

    Args:
        username (str): User's username
        snowflake (int): User's account ID
        avatar (Union[str, None]): User's avatar URL
    """
    current_date = datetime.now()
    db = get_db()
    current_app.logger.info(f"Adding user {username} to User table")
    db.execute(
        "INSERT INTO user (username, snowflake, avatar, last_login_date) VALUES (?, ?, ?, ?)",
        (
            username,
            snowflake,
            avatar,
            current_date.strftime("%Y-%m-%d %H:%M:%S"),
        ),
    )
    db.commit()
    
    
def get_user(snowflake: int) -> User:
    """Returns a user from the db if one exists, else creates a new user in the database

    Args:
        username (str): User's username
        snowflake (int): User's account ID
        avatar (Union[str, None]): User's avatar URL
        
    Returns:
        User: user object
    """
    db = get_db()
    q = db.execute("SELECT * FROM user WHERE snowflake = ?", (snowflake,))
    result = q.fetchone()

    if result:
        return parse_obj_as(User, result)
    return None
    


def update_login_time(snowflake: int) -> None:
    """Update the user's last logged in time

    Args:
        snowflake (int): User's ID
    """
    current_date = datetime.now()
    db = get_db()
    db.execute(
        "UPDATE user SET last_login_date = ? WHERE snowflake = ?",
        (current_date.strftime("%Y-%m-%d %H:%M:%S"), snowflake),
    )
    db.commit()

def update_user_avatar(snowflake: int, avatar: str) -> None:
    db = get_db()
    db.execute(
        "UPDATE user SET avatar = ? WHERE snowflake = ?",
        (avatar,snowflake),
    )
    db.commit()
