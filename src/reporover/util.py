"""Utility functions for the reporover command-line interface."""

import json
from pathlib import Path
from typing import List

from rich.progress import Progress


def print_json_string(json_string: str, progress: Progress) -> None:
    """Convert JSON string to dictionary and print each key-value pair."""
    # convert the JSON string to a dictionary
    dictionary = json.loads(json_string)
    # display each key-value pair in the dictionary;
    # useful for debugging purposes when there is a
    # response back from the GitHub API after an error
    for key, value in dictionary.items():
        progress.console.print(f"  {key}: {value}")


def read_usernames_from_json(file_path: Path) -> List[str]:
    """Read usernames from a JSON file."""
    # read the JSON file and load contents
    with file_path.open("r") as file:
        data = json.load(file)
    # return the list of usernames in JSON file
    return data.get("usernames", [])
