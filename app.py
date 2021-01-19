from overpass import create_app
import logging
import config
import os

if os.environ.get("FLASK_ENV") == "development":
    app = create_app(config.DevConfig())
    app.logger.info("Development environment detected.")
else:
    app = create_app(config.ProdConfig())
    gunicorn_logger = logging.getLogger("gunicorn.error")
    app.logger.handlers = gunicorn_logger.handlers
    app.logger.setLevel(gunicorn_logger.level)
    app.logger.info("No environment variable set, using production config.")

if __name__ == "__main__":
    app.run()