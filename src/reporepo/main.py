"""Main module for the reporepo command-line interface."""

import json
from enum import Enum
from pathlib import Path
from typing import List, Optional

import requests
import typer
from rich.console import Console
from rich.progress import BarColumn, Progress, TextColumn
from typer import Typer

# define the Typer app that will be used
# to run the Typer-based command-line interface
app = Typer()

# create a default console
console = Console()


class StatusCode(Enum):
    """Define the status codes for the GitHub API."""

    SUCCESS = 204
    BAD_REQUEST = 400
    UNAUTHORIZED = 401
    FORBIDDEN = 403
    NOT_FOUND = 404
    UNPROCESSABLE_ENTITY = 422
    INTERNAL_SERVER_ERROR = 500


class GitHubAccessLevel(Enum):
    """Define the access levels for GitHub repositories."""

    READ = "read"
    TRIAGE = "triage"
    WRITE = "write"
    MAINTAIN = "maintain"
    ADMIN = "admin"


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


def modify_user_access(  # noqa: PLR0913
    github_organization_url: str,
    repo_prefix: str,
    username: str,
    access_level: GitHubAccessLevel,
    token: str,
    progress: Progress,
) -> None:
    """Change user access to read."""
    # extract the repository name from the URL
    organization_name = github_organization_url.split("github.com/")[1].split(
        "/"
    )[0]
    # define the full name of the repository that involves
    # the prefix of the repository a separating dash and
    # then the name of the user; note that this is the standard
    # adopted by GitHub repositories created by GitHub Classroom
    full_repository_name = repo_prefix + "-" + username
    full_name_for_api = organization_name + "/" + full_repository_name
    # define the API URL for the request
    api_url = f"https://api.github.com/repos/{full_name_for_api}/collaborators/{username}"
    # headers for the request
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json",
    }
    # data for the request
    data = {"permission": access_level.value}
    # make the PUT request to change the user's permission
    response = requests.put(api_url, headers=headers, json=data)
    # check if the request was successful
    # display positive configuration since change of the access level worked
    if response.status_code == StatusCode.SUCCESS.value:
        progress.console.print(
            f"󰄬 Changed {username}'s access to '{access_level.value}'"
        )
    # display error message since the change of the access level did not work
    else:
        # display the basic error message
        progress.console.print(
            f" Failed to change access for {username}: {response.status_code}"
        )
        # display all of the rest of the details in the string
        # that encodes the JSON response from the GitHub API
        print_json_string(response.text, progress)


@app.command()
def cli(  # noqa: PLR0913
    github_org_url: str = typer.Argument(
        ..., help="URL of GitHub organization"
    ),
    repo_prefix: str = typer.Argument(
        ..., help="Prefix for GitHub repository"
    ),
    usernames_file: Path = typer.Argument(
        ..., help="Path to JSON file with usernames"
    ),
    token: str = typer.Argument(..., help="GitHub token for authentication"),
    username: Optional[List[str]] = typer.Option(
        default=None, help="List of usernames' accounts to modify"
    ),
    access_level: GitHubAccessLevel = typer.Option(
        GitHubAccessLevel.READ.value,
        help="The access level for user",
    ),
):
    """Modify a user's access to GitHub repository."""
    # display the welcome message
    console.print(":sparkles: RepoRepo helps you 'repo' a GitHub repository!")
    console.print()
    # extract the usernames from the TOML file
    usernames_parsed = read_usernames_from_json(usernames_file)
    # if the user has provided a list of usernames only use
    # those usernames as long as they are inside of the parsed usernames
    # (i.e., the usernames variable lets you select a subset of those
    # names that are specified in the JSON file of usernames)
    if username:
        usernames_parsed = list(set(username) & set(usernames_parsed))
    # iterate through all of the usernames
    # display a progress bar based on the
    # number of usernames in the JSON file
    with Progress(
        "[progress.description]{task.description}",
        BarColumn(),
        "[progress.percentage]{task.percentage:>3.0f}%",
        TextColumn("[progress.completed]{task.completed}/{task.total}"),
    ) as progress:
        task = progress.add_task(
            "[green]Modifying User's Access", total=len(usernames_parsed)
        )
        # modify the access for the current user
        for current_username in usernames_parsed:
            modify_user_access(
                github_org_url,
                repo_prefix,
                current_username,
                access_level,
                token,
                progress,
            )
            # take the next step in the progress bar
            progress.advance(task)
