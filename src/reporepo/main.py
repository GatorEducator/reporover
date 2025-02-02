"""Main module for the reporepo command-line interface."""

import json
from enum import Enum

import requests
import typer
from rich.console import Console
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


def print_json_string(json_string: str):
    """Convert JSON string to dictionary and print each key-value pair."""
    dictionary = json.loads(json_string)
    for key, value in dictionary.items():
        console.print(f"\t{key}: {value}")


def modify_user_access(
    github_organization_url: str,
    repo_prefix: str,
    username: str,
    access_level: GitHubAccessLevel,
    token: str,
) -> None:
    """Change user access to read."""
    # extract the repository name from the URL
    organization_name = github_organization_url.split("github.com/")[1].split(
        "/"
    )[0]
    console.print(organization_name)
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
        console.print(f"󰄬 Changed {username}'s access to 'read'")
    # display error message since the change of the access level did not work
    else:
        console.print(
            f" Failed to change access for {username}: {response.status_code}"
        )
        print_json_string(response.text)


@app.command()
def cli(
    github_org_url: str = typer.Argument(
        ..., help="The URL of GitHub organization"
    ),
    repo_prefix: str = typer.Argument(
        ..., help="The prefix for GitHub repository"
    ),
    username: str = typer.Argument(
        ..., help="The username subject to access change"
    ),
    token: str = typer.Argument(
        ..., help="The GitHub token for authentication"
    ),
    access_level: GitHubAccessLevel = typer.Option(
        GitHubAccessLevel.READ.value,
        help="The access level for user",
    ),
):
    """Define command-line interface for the reporepo program."""
    console.print(":sparkles: RepoRepo helps you `repo` a GitHub repository!")
    console.print()
    modify_user_access(
        github_org_url, repo_prefix, username, access_level, token
    )
