from flask import redirect, url_for, Blueprint, abort
from flask.json import jsonify

# from flask import current_app as app
from flask_discord import requires_authorization
from overpass import discord

DISCORD_GUILD_ID = 687702747813773457

auth = Blueprint("auth", __name__)


@auth.route("/login/")
def login():
    return discord.create_session(scopes=["identify", "email", "guilds"])


@auth.route("/callback/")
def callback():
    discord.callback()
    return redirect(url_for(".verify"))


@auth.errorhandler(403)
def redirect_unauthorized(e):
    return (
        jsonify(
            {"message": "Your Discord user is not authorized to use this application."}
        ),
        403,
    )


@auth.route("/verify/")
@requires_authorization
def verify():
    guilds = discord.fetch_guilds()
    user_is_in_guild = next((i for i in guilds if i.id == DISCORD_GUILD_ID), False)
    if user_is_in_guild:
        return redirect(url_for(".me"))
    else:
        return abort(403)


@auth.route("/me/")
@requires_authorization
def me():
    user = discord.fetch_user()
    return jsonify(user.__dict__)
