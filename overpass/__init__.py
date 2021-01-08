from flask import Flask
from overpass.secrets import (
    DISCORD_CLIENT_ID,
    DISCORD_CLIENT_SECRET,
    DISCORD_REDIRECT_URI,
)
from flask_discord import DiscordOAuth2Session
from flask_login import LoginManager
import os
from overpass.db import init_app, close_db, init_db_command

os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"
discord = DiscordOAuth2Session()
login = LoginManager()


def create_app():
    app = Flask(__name__)
    app.secret_key = os.urandom(16)
    app.teardown_appcontext(close_db)
    app.cli.add_command(init_db_command)

    app.config["DATABASE"] = "overpass.db"
    app.config["DISCORD_CLIENT_ID"] = DISCORD_CLIENT_ID
    app.config["DISCORD_CLIENT_SECRET"] = DISCORD_CLIENT_SECRET
    app.config["DISCORD_REDIRECT_URI"] = DISCORD_REDIRECT_URI

    discord.init_app(app)
    login.init_app(app)
    init_app(app)

    with app.app_context():
        # Imports are done here to prevent circular import errors when
        # importing extensions from this file
        from overpass.auth import auth
        from overpass.stream_api import bp as stream
        from overpass.rtmp_server_api import bp as rtmp

        app.register_blueprint(auth)
        app.register_blueprint(stream, url_prefix="/api/stream")
        app.register_blueprint(rtmp, url_prefix="/api/rtmp")

        @app.route("/")
        def home() -> str:
            return "Hello world!"

        return app
