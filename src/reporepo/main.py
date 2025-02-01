"""Main module for the reporepo command-line interface."""

import requests
import typer
from rich.console import Console
from typer import Typer

# define the Typer app that will be used
# to run the Typer-based command-line interface
app = Typer()

# create a default console
console = Console()


def change_user_access(repo_url: str, username: str, token: str):
    """Change user access to read."""
    # extract the repository name from the URL
    repo_name = repo_url.split("github.com/")[1]
    # GitHub API URL to add a collaborator
    api_url = (
        f"https://api.github.com/repos/{repo_name}/collaborators/{username}"
    )
    # headers for the request
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json",
    }
    # data for the request
    data = {"permission": "read"}
    # make the PUT request to change the user's permission
    response = requests.put(api_url, headers=headers, json=data)
    # check if the request was successful
    if response.status_code == 204:
        console.print(f"successfully changed {username}'s access to 'read'.")
    else:
        console.print(
            f"failed to change access: {response.status_code} - {response.text}"
        )


@app.command()
def cli(
    repo_url: str = typer.Argument(..., help="The URL of the repository"),
    username: str = typer.Argument(
        ..., help="The username to change access for"
    ),
    token: str = typer.Argument(
        ..., help="The GitHub token for authentication"
    ),
):
    """Define command-line interface for the apparent program."""
    console.print("Hello, world!")
    change_user_access(repo_url, username, token)
