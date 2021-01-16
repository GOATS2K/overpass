from overpass import create_app
from dotenv import load_dotenv
import logging

load_dotenv(".env")
app = create_app()

if __name__ != "__main__":
    gunicorn_logger = logging.getLogger("gunicorn.error")
    app.logger.handlers = gunicorn_logger.handlers
    app.logger.setLevel(gunicorn_logger.level)
    app.logger.info(f"Secret key: {app.secret_key}")

if __name__ == "__main__":
    app.run()
