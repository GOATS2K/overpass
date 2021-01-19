import os
from dotenv import load_dotenv

load_dotenv(".env")


class Config(object):
    DEBUG = False
    TESTING = False
    DATABASE = "overpass.db"
    DISCORD_CLIENT_ID = os.environ.get("DISCORD_CLIENT_ID")
    DISCORD_CLIENT_SECRET = os.environ.get("DISCORD_CLIENT_SECRET")
    DISCORD_REDIRECT_URI = os.environ.get("DISCORD_REDIRECT_URI")


class DevConfig(Config):
    DEBUG = True
    DATABASE = "overpass-dev.db"
    SECRET_KEY = os.urandom(16)


class ProdConfig(Config):
    SECRET_KEY = os.environ.get("OVERPASS_SECRET_KEY").encode()
    SESSION_COOKIE_SECURE = True
    REMEMBER_COOKIE_SECURE = True
