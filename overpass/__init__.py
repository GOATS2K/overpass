from flask import Flask
from flask.templating import render_template
from flask_discord import DiscordOAuth2Session
import os
from overpass.db import init_app, close_db, init_db_command
from dotenv import load_dotenv
import config

basedir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(basedir, ".env"))


os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"
discord = DiscordOAuth2Session()


def create_app(config_instance):
    app = Flask(__name__)
    app.config.from_object(config_instance)

    app.teardown_appcontext(close_db)
    app.cli.add_command(init_db_command)

    discord.init_app(app)
    init_app(app)

    with app.app_context():
        # Imports are done here to prevent circular import errors when
        # importing extensions from this file
        from overpass.auth import auth
        from overpass.stream_api import bp as stream
        from overpass.rtmp_server_api import bp as rtmp
        from overpass.index import bp as index
        from overpass.archive import bp as archive
        from overpass.hls import bp as hls
        from overpass.watch import bp as watch
        from overpass.profile import bp as profile
        from overpass.manage_user import bp as manage

        app.register_blueprint(index)
        app.register_blueprint(auth, url_prefix="/auth")
        app.register_blueprint(stream, url_prefix="/stream")
        app.register_blueprint(rtmp, url_prefix="/api/rtmp")
        app.register_blueprint(archive, url_prefix="/archive")
        app.register_blueprint(hls, url_prefix="/hls")
        app.register_blueprint(watch, url_prefix="/watch")
        app.register_blueprint(profile, url_prefix="/profile")
        app.register_blueprint(manage, url_prefix="/manage")

        from overpass.jinja_filters import nl2br

        app.add_template_filter(nl2br)

        @app.errorhandler(404)
        def page_not_found(e):
            return render_template("alert.html", error="Page not found."), 404

        @app.errorhandler(403)
        def forbidden(e):
            return (
                render_template(
                    "alert.html", error="You are not allowed to perform this action."
                ),
                403,
            )

        return app
