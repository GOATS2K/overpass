from flask import Flask
from flask_discord import DiscordOAuth2Session
import os
from overpass.db import init_app, close_db, init_db_command
from dotenv import load_dotenv

basedir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(basedir, ".env"))


os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"
discord = DiscordOAuth2Session()


def create_app():
    app = Flask(__name__)
    secret_key = os.environ.get("OVERPASS_SECRET_KEY")

    try:
        app.secret_key = secret_key.encode()
    except NoneType:
        raise ValueError("The environment variable OVERPASS_SECRET_KEY is not set!")

    app.teardown_appcontext(close_db)
    app.cli.add_command(init_db_command)

    app.config["DATABASE"] = "overpass.db"
    app.config["DISCORD_CLIENT_ID"] = os.environ.get("DISCORD_CLIENT_ID")
    app.config["DISCORD_CLIENT_SECRET"] = os.environ.get("DISCORD_CLIENT_SECRET")
    app.config["DISCORD_REDIRECT_URI"] = os.environ.get("DISCORD_REDIRECT_URI")

    discord.init_app(app)
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
