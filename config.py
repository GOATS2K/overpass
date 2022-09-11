from genericpath import exists
import os
from pathlib import Path
from dotenv import load_dotenv

if Path(".env").exists():
    load_dotenv(".env")


def get_secret_key():
    env_key = os.environ.get("OVERPASS_SECRET_KEY")
    if env_key:
        return env_key.encode()

    print(
        "No secret key found, please set the environment variable OVERPASS_SECRET_KEY"
    )
    print("Generating key for temporary usage...")
    return os.urandom(16)


def get_database_directory(dev: bool = False) -> str:
    database_name = "overpass.db" if not dev else "overpass-dev.db"
    env_database_path = os.environ.get("OVERPASS_DATABASE_PATH")
    if env_database_path:
        database_dir = Path(env_database_path)
        database_dir.mkdir(exist_ok=True)
        return database_dir / database_name
    return database_name


class Config(object):
    DEBUG = False
    TESTING = False
    DATABASE = get_database_directory()
    DISCORD_CLIENT_ID = os.environ.get("DISCORD_CLIENT_ID")
    DISCORD_CLIENT_SECRET = os.environ.get("DISCORD_CLIENT_SECRET")
    DISCORD_REDIRECT_URI = os.environ.get("DISCORD_REDIRECT_URI")


class DevConfig(Config):
    DEBUG = True
    DATABASE = get_database_directory(dev=True)
    SECRET_KEY = get_secret_key()


class ProdConfig(Config):
    SECRET_KEY = get_secret_key()
    SESSION_COOKIE_SECURE = True
    REMEMBER_COOKIE_SECURE = True
