from flask import request

# from overpass.app import app


def info() -> str:
    req_data = request.form
    print(req_data)
    return "This doesn't do anything yet."
