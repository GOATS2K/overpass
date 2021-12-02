from typing import Any, Dict, List
import click
from flask import current_app, g
from flask.app import Flask
from flask.cli import with_appcontext
import sqlite3


def make_dicts(cursor: sqlite3.Cursor, row: sqlite3.Row) -> dict:
    return dict(
        (cursor.description[idx][0], value) for idx, value in enumerate(row)
    )


def get_db() -> sqlite3.Connection:
    if "db" not in g:
        g.db = sqlite3.connect(
            current_app.config["DATABASE"],
            detect_types=sqlite3.PARSE_DECLTYPES,
        )
        g.db.row_factory = make_dicts

    return g.db


def close_db(e=None) -> None:
    db = g.pop("db", None)

    if db is not None:
        db.close()


def query_many(query: str, args: Any = ()) -> List[Dict[str, Any]]:
    cur = get_db().execute(query, args)
    rv = cur.fetchall()
    cur.close()
    return rv


def query_one(query: str, args: Any = ()) -> Dict[str, Any]:
    cur = get_db().execute(query, args)
    rv = cur.fetchall()
    cur.close()
    return rv[0] if rv else {}


def init_db() -> None:
    db = get_db()

    with current_app.open_resource("schema.sql") as f:
        db.executescript(f.read().decode("utf8"))


def init_app(app: Flask):
    app.teardown_appcontext(close_db)
    app.cli.add_command(init_db_command)


@click.command("init-db")
@with_appcontext
def init_db_command() -> None:
    """Clear the existing data and create new tables."""
    click.echo(
        f"You're now about to initialize the following database file: {current_app.config['DATABASE']}"
    )
    if click.confirm("Are you sure about this?"):
        init_db()
        click.secho("Initialized the database.", fg="green")
    else:
        click.secho("Initialization aborted.", fg="red")
