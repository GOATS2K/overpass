from flask import redirect, url_for, Blueprint

# from flask import current_app as app
from flask_discord import requires_authorization, Unauthorized
from overpass import discord

auth = Blueprint("auth", __name__)


@auth.route("/login/")
def login():
    return discord.create_session()


@auth.route("/callback/")
def callback():
    discord.callback()
    return redirect(url_for(".me"))


@auth.errorhandler(Unauthorized)
def redirect_unauthorized(e):
    return redirect(url_for("login"))


@auth.route("/me/")
@requires_authorization
def me():
    user = discord.fetch_user()
    return f"""
        <html>
            <head>
                <title>{user.name}</title>
            </head>
            <body>
                <img src='{user.avatar_url}' />
            </body>
        </html>"""
