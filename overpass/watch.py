from typing import Any, Dict, Text

from flask import render_template

from overpass.archive import get_archived_streams


def get_single_archived_stream(
    unique_id: str, all_metadata: bool = False, private: bool = False
) -> Dict[str, Any]:
    """Get a single stream from the archive

    Args:
        unique_id (str): The stream's unique ID.

        all_metadata (bool, optional): Return all metadata about the stream.
        Defaults to False.

        private (bool, optional):
        Include streams that aren't publically archived.
        Defaults to False.

    Returns:
        Dict[str, Any]: Dict containing information about the stream.
    """
    archived_streams = get_archived_streams(
        all_metadata=all_metadata, private=private
    )
    stream = next(
        stream
        for stream in archived_streams
        if stream["unique_id"] == unique_id
    )
    return stream


def return_stream_page(unique_id: str, stream: Dict[str, Any]) -> Text:
    """Helper function used in the watch_stream function

    Args:
        unique_id (str): The stream's unique ID.
        stream (Dict[str, Any]): Metadata about the stream.

    Returns:
        Text: Static page rendered by Flask.
    """
    return render_template(
        "watch.html",
        id=unique_id,
        stream=stream,
        archive_link=stream["download"],
    )
