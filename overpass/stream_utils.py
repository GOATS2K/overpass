from overpass.db import query_db
from flask import current_app


def get_unique_stream_id_from_stream_key(stream_key):
    res = query_db(
        "SELECT unique_id FROM stream WHERE stream_key = ?", [stream_key], one=True
    )
    return res["unique_id"]


def get_stream_key_from_unique_id(unique_id):
    res = query_db(
        "SELECT stream_key FROM stream WHERE unique_id = ?", [unique_id], one=True
    )
    return res["stream_key"]


def rewrite_stream_playlist(path, stream_key):
    current_app.logger.info(f"Rewriting playlist for {stream_key}")
    with open(f"{path}/{stream_key}.m3u8", "r") as infile:
        lines = infile.readlines()

    with open(f"{path}/{stream_key}-index.m3u8", "w+") as outfile:
        outfile.seek(0)
        outfile.truncate()
        for line in lines:
            outfile.write(line.replace(f"{stream_key}-", ""))
