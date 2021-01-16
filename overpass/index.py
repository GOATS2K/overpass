from flask import Blueprint
from flask.templating import render_template
from overpass import discord
from overpass.stream_api import get_current_livestreams

bp = Blueprint("index", __name__)


@bp.route("/")
def home():
    auth = discord.authorized
    if not auth:
        return render_template("index.html", authorized=auth)
    else:
        streams = get_current_livestreams()
        if streams:
            return render_template("index.html", authorized=auth, streams=streams)
        else:
            return render_template("index.html", authorized=auth)
