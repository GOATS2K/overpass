from flask import Flask
from overpass.secrets import (
    DISCORD_CLIENT_ID,
    DISCORD_CLIENT_SECRET,
    DISCORD_REDIRECT_URI,
)
from flask_discord import DiscordOAuth2Session
import os
from overpass.db import init_app, close_db, init_db_command

discord = DiscordOAuth2Session()


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
    init_app(app)

    with app.app_context():
        # Imports are done here to prevent circular import errors when
        # importing extensions from this file
        from overpass.auth import auth

        app.register_blueprint(auth)

        @app.route("/")
        def home() -> str:
            return "Hello world!"

        return app
