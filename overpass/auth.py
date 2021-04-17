# flake8: noqa E501

from typing import Any, Text, Union
from flask import redirect, url_for, Blueprint, abort, session, current_app
from flask.json import jsonify
from flask.templating import render_template
from flask.wrappers import Response

# from flask import current_app as app
from flask_discord import requires_authorization, Unauthorized, RateLimited
from overpass import discord
from overpass.db import get_db
from datetime import datetime
import os

DISCORD_GUILD_ID = os.environ.get("DISCORD_GUILD_ID") or ""

auth = Blueprint("auth", __name__)


def verify() -> bool:
    """Verifies if user exists in the Discord guild

    Returns:
        bool: User exists in guild
    """
    guilds = discord.fetch_guilds()
    user_is_in_guild = next((i for i in guilds if i.id == int(DISCORD_GUILD_ID)), False)
    if user_is_in_guild:
        return True
    else:
        return False


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
        (username, snowflake, avatar, current_date.strftime("%Y-%m-%d %H:%M:%S")),
    )
    db.commit()


def check_if_user_exists(snowflake: int) -> bool:
    """Returns True if user exists in database

    Args:
        snowflake (int): User's ID

    Returns:
        bool: User exists in database
    """
    db = get_db()
    q = db.execute("SELECT * FROM user WHERE snowflake = ?", (snowflake,))
    result = q.fetchone()

    if result:
        return True
    else:
        return False


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


@auth.route("/login/")
def login() -> Any:
    """Redirect user to Discord's SSO page

    Returns:
        Any: Redirection to Discord's SSO page
    """
    return discord.create_session(scope=["identify", "guilds"])


@auth.route("/logout/")
def logout() -> Text:
    """Revoke a user's session

    Returns:
        Text: Flask rendered template
    """
    discord.revoke()
    return render_template("alert.html", info="You've been logged out.")


@auth.route("/callback/")
def callback() -> Any:
    """Callback endpoint for SSO service

    Returns:
        Any: Redirect to home page if everything went well, else return 401.
    """
    try:
        discord.callback()
        if DISCORD_GUILD_ID:
            if not verify():
                # When the callback succeeds, the token for the user gets set in memory
                # Since the user isn't a member of the guild, we reset the session
                # to prevent access to the API
                session.clear()
                return abort(401)

        resp = discord.fetch_user()
        # Assume successful login
        if not check_if_user_exists(resp.id):
            add_user(resp.username, resp.id, resp.avatar_url)
        else:
            current_app.logger.info(f"User {resp.username} has just signed in")
            # Update last login time
            update_login_time(resp.id)

        return redirect(url_for("index.home"))
    except RateLimited:
        return "We are currently being rate limited, try again later."


@auth.errorhandler(Unauthorized)
def redirect_discord_unauthorized(e) -> Any:
    return redirect(url_for("auth.login"))


# Runs when abort(401) is called.
@auth.errorhandler(401)
def redirect_unauthorized(e) -> Any:
    return (
        jsonify(
            {"message": "Your Discord user is not authorized to use this application."}
        ),
        401,
    )

