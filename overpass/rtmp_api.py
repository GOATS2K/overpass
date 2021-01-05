from flask import request, Blueprint, redirect, url_for
import uuid
from flask_discord import requires_authorization, Unauthorized

# from overpass.app import app

bp = Blueprint("api", __name__)


@bp.errorhandler(Unauthorized)
def redirect_discord_unauthorized(e):
    return redirect(url_for("auth.login"))


@bp.before_request
@requires_authorization
def require_auth():
    pass


@bp.route("/info")
def info() -> str:
    return "This doesn't do anything yet."


@bp.route("/stream/start", methods=["POST"])
def generate_stream_key():
    stream_key = str(uuid.uuid1())[0:8]
    return stream_key

