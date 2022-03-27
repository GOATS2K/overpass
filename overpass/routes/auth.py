from typing import Any, Text

from flask import Blueprint, abort, current_app, redirect, session, url_for
from flask.templating import render_template
from matplotlib.pyplot import disconnect
from flask_discord import RateLimited, Unauthorized
from overpass import discord
from overpass.auth import (
    DISCORD_GUILD_ID,
    add_user,
    get_user,
    update_login_time,
    update_user_avatar,
    verify,
)

auth = Blueprint("auth", __name__)


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
        discord_user = discord.fetch_user()
        if DISCORD_GUILD_ID:
            if not verify():
                # When the callback succeeds, the token for the user gets
                # set in memory
                # Since the user isn't a member of the guild
                # we reset the session to prevent access to the API
                current_app.logger.error(
                    f"Username {discord_user.username} with ID {discord_user.id} is not a member of the target guild"  # noqa: E501
                )
                session.clear()
                return abort(401)

        # Assume successful login
        user = get_user(discord_user.id)
        if user:
            if discord_user.avatar_url != user.avatar:
                update_user_avatar(user.id, discord_user.avatar_url) # user in db becomes source of truth
                
            update_login_time(user.id)
            current_app.logger.info(f"User {user.username} has just signed in")
        else:
            add_user(discord_user.username, discord_user.id, discord_user.avatar_url)
                       
        return redirect(url_for("index.home"))
    except RateLimited:
        return "We are currently being rate limited, try again later."


@auth.errorhandler(Unauthorized)
def redirect_discord_unauthorized(e) -> Any:
    return redirect(url_for("auth.login"))


# Runs when abort(401) is called.
@auth.errorhandler(401)
def redirect_unauthorized(e) -> Any:
    return """
    <h2>Your Discord user is not authorized to use this application.</h2>
    <p>Please verify that you are a member of the target Discord server.</p>
    """
