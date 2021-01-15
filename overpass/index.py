from flask import Blueprint
from flask.templating import render_template
from overpass import discord

bp = Blueprint("index", __name__)


@bp.route("/")
def home():
    auth = discord.authorized
    if not auth:
        return render_template("index.html", authorized=auth)
    else:
        user = discord.fetch_user()
        return render_template("index.html", authorized=auth, user=user)
