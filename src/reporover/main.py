"""Main module for the reporover command-line interface."""

import base64
import json
from enum import Enum
from pathlib import Path
from typing import Callable, List, Optional, Union

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

    WORKING = 200
    CREATED = 201
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


class GitHubPullRequestNumber(Enum):
    """Define the pull request number(s) for the GitHub repositories."""

    ONE = 1
    TWO = 2
    THREE = 3
    DEFAULT = 1


class PullRequestMessages(Enum):
    """Define the pull request messages to leave in the GitHub repositories."""

    MODIFIED_TO_PHRASE = (
        "Your access level for this GitHub repository has been modified to"
    )
    ASSISTANCE_SENTENCE = "Please contact the course instructor for assistance with access to your repository."


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


def display_welcome_message() -> None:
    """Display the welcome message for all reporover commands."""
    console.print()
    console.print(
        ":sparkles: RepoRover manages and analyzes remote GitHub repositories! Arf!"
    )


def modify_user_access(  # noqa: PLR0913
    github_organization_url: str,
    repo_prefix: str,
    username: str,
    access_level: GitHubAccessLevel,
    token: str,
    progress: Progress,
    put_request_function: Callable = requests.put,
) -> Union[StatusCode, None]:
    """Change user access to read."""
    # define the status codes for the request
    request_status_code = None
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
    response = put_request_function(api_url, headers=headers, json=data)
    # check if the request was successful
    # display positive configuration since change of the access level worked
    if response.status_code == StatusCode.SUCCESS.value:
        progress.console.print(
            f"󰄬 Changed {username}'s access to '{access_level.value}' in"
            + f" {full_repository_name}"
        )
        request_status_code = StatusCode.SUCCESS
    # display error message since the change of the access level did not work
    else:
        # display the basic error message
        progress.console.print(
            f" Failed to change {username}'s access to '{access_level.value}' in"
            + f" {full_repository_name}\n"
            + f"  Diagnostic: {response.status_code}"
        )
        # display all of the rest of the details in the string
        # that encodes the JSON response from the GitHub API
        print_json_string(response.text, progress)
    return request_status_code


def leave_pr_comment(  # noqa: PLR0913
    github_organization_url: str,
    repo_prefix: str,
    username: str,
    access_level: Union[GitHubAccessLevel, None],
    message: str,
    pr_number: int,
    token: str,
    progress: Progress,
) -> None:
    """Leave a comment on the first pull request of the repository."""
    # extract the organization name from the URL
    organization_name = github_organization_url.split("github.com/")[1].split(
        "/"
    )[0]
    # define the full name of the repository
    full_repository_name = f"{repo_prefix}-{username}"
    full_name_for_api = f"{organization_name}/{full_repository_name}"
    # define the API URL for the pull request comments
    pr_comments_url = f"https://api.github.com/repos/{full_name_for_api}/issues/{pr_number}/comments"
    # headers for the request
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json",
    }
    # build up the data for the request,
    # starting with an empty message
    complete_message = ""
    # check if the access level is specified
    # and use it to create the complete message
    if access_level:
        complete_message = (
            f"Hello @{username}! {PullRequestMessages.MODIFIED_TO_PHRASE.value} `{access_level.value}`. "
            + f"{PullRequestMessages.ASSISTANCE_SENTENCE.value} "
            + f"{message}"
        )
    # there is no access level specified and thus
    # only the specified message is provided
    else:
        complete_message = f"Hello @{username}! " + f"{message}"
    data = {"body": complete_message}
    # make the POST request to leave the comment
    response = requests.post(pr_comments_url, headers=headers, json=data)
    # check if the request was successful
    if response.status_code == StatusCode.CREATED.value:
        progress.console.print(
            f"󰄬 Commented on the pull request number {pr_number} for GitHub repository {full_repository_name}"
        )
    else:
        progress.console.print(
            f" Failed to comment on pull request {pr_number} for GitHub repository {full_repository_name}\n"
            + f"  Diagnostic: {response.status_code}"
        )
        print_json_string(response.text, progress)


def get_github_actions_status(
    github_organization_url: str,
    repo_prefix: str,
    username: str,
    token: str,
    progress: Progress,
) -> None:
    """Report the GitHub Actions status for a repository."""
    # extract the organization name from the URL
    organization_name = github_organization_url.split("github.com/")[1].split(
        "/"
    )[0]
    # define the full name of the repository
    full_repository_name = f"{repo_prefix}-{username}"
    full_name_for_api = f"{organization_name}/{full_repository_name}"
    # define the API URL for the GitHub Actions status
    api_url = f"https://api.github.com/repos/{full_name_for_api}/actions/runs"
    # headers for the request
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json",
    }
    # make the GET request to get the GitHub Actions status
    response = requests.get(api_url, headers=headers)
    # check if the request was successful
    if response.status_code == StatusCode.WORKING.value:
        # there are workflow runs and they should be displayed
        runs = response.json().get("workflow_runs", [])
        if runs:
            latest_run = runs[0]
            status = latest_run.get("status", "unknown")
            conclusion = latest_run.get("conclusion", "unknown")
            progress.console.print(
                f"- Latest GitHub Actions run for {full_repository_name}:\n"
                f"  Status: {status}\n"
                f"  Conclusion: {conclusion}"
            )
        # could not find any workflow runs to display
        else:
            progress.console.print(
                f"? No GitHub Actions runs found for {full_repository_name}"
            )
    # display error message since the request did not work
    else:
        progress.console.print(
            f" Failed to get GitHub Actions status for {full_repository_name}\n"
            f"  Diagnostic: {response.status_code}"
        )
        print_json_string(response.text, progress)


def commit_files_to_repo(  # noqa: PLR0913
    github_organization_url: str,
    repo_prefix: str,
    username: str,
    token: str,
    directory: Path,
    files: List[Path],
    commit_message: str,
    destination_directory: Path,
    progress: Progress,
) -> None:
    """Commit files to a GitHub repository."""
    # extract the organization name from the URL
    organization_name = github_organization_url.split("github.com/")[1].split(
        "/"
    )[0]
    # define the full name of the repository
    full_repository_name = f"{repo_prefix}-{username}"
    full_name_for_api = f"{organization_name}/{full_repository_name}"
    # define the API URL for the repository contents
    api_url = f"https://api.github.com/repos/{full_name_for_api}/contents/"
    # headers for the request
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json",
    }
    # iterate over each file to commit
    for file_path in files:
        # read the file content
        file_content = (directory / file_path).read_bytes()
        # encode the file content in base64
        encoded_content = base64.b64encode(file_content).decode()
        # define the data for the request
        data = {
            "message": commit_message,
            "content": encoded_content,
            "branch": "main",
        }
        # construct the full path for the file in the repository
        destination_path = destination_directory / file_path.name
        # make the PUT request to commit the file
        response = requests.put(
            api_url + destination_path.as_posix(), headers=headers, json=data
        )
        # check if the request was successful and display
        # the appropriate message based on the status code
        if response.status_code in [
            StatusCode.CREATED.value,
            StatusCode.SUCCESS.value,
        ]:
            progress.console.print(
                f"󰄬 Committed {file_path.name} to {full_repository_name} in directory '{destination_directory}'"
            )
        # something went wrong and thus display the error message;
        # note that it is not possible to commit the same file if
        # there have not been changes to it. This means that a request
        # of this nature will lead to this error message.
        else:
            progress.console.print(
                f" Failed to commit {file_path.name} to {full_repository_name} in directory '{destination_directory}'\n"
                f"  Diagnostic: {response.status_code}"
            )
            print_json_string(response.text, progress)


@app.command()
def access(  # noqa: PLR0913
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
        default=None, help="One or more usernames' accounts to modify"
    ),
    pr_number: int = typer.Option(
        GitHubPullRequestNumber.DEFAULT.value,
        help="Pull request number in GitHub repository",
    ),
    pr_message: str = typer.Option(
        "",
        help="Pull message for the GitHub repository",
    ),
    access_level: GitHubAccessLevel = typer.Option(
        GitHubAccessLevel.READ.value,
        help="The access level for user",
    ),
):
    """Modify user access to GitHub repositories."""
    # display the welcome message
    display_welcome_message()
    # display details about this command
    console.print(
        f":sparkles: Modifying repositories in this GitHub organization: {github_org_url}"
    )
    console.print(
        f":sparkles: Changing all repository access levels to '{access_level.value}' for each valid user"
    )
    console.print()
    # extract the usernames from the TOML file
    usernames_parsed = read_usernames_from_json(usernames_file)
    # if there exists a list of usernames only use those usernames as long
    # as they are inside of the parsed usernames, the complete list
    # (i.e., the username variable lets you select a subset of those
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
        # and then leave a comment on the existing pull
        # request (PR); note that this works because GitHub
        # classroom already creates a PR when the person
        # accepts an assignment. However, it is also possible
        # to specify the PR number on the command line.
        for current_username in usernames_parsed:
            # note that passing the progress bar to
            # each of the following functions allows their
            # output to be displayed as integrated to the
            # progress bar that shows task completion
            # modify the user's access level
            modify_user_access(
                github_org_url,
                repo_prefix,
                current_username,
                access_level,
                token,
                progress,
                requests.put,
            )
            # leave a comment on the existing PR
            # to notify the user of the change
            leave_pr_comment(
                github_org_url,
                repo_prefix,
                current_username,
                access_level,
                pr_message,
                pr_number,
                token,
                progress,
            )
            # take the next step in the progress bar
            progress.advance(task)


@app.command()
def comment(  # noqa: PLR0913
    github_org_url: str = typer.Argument(
        ..., help="URL of GitHub organization"
    ),
    repo_prefix: str = typer.Argument(
        ..., help="Prefix for GitHub repository"
    ),
    usernames_file: Path = typer.Argument(
        ..., help="Path to JSON file with usernames"
    ),
    pr_message: str = typer.Argument(
        ...,
        help="Pull request number in GitHub repository",
    ),
    token: str = typer.Argument(..., help="GitHub token for authentication"),
    username: Optional[List[str]] = typer.Option(
        default=None, help="One or more usernames' accounts to modify"
    ),
    pr_number: int = typer.Option(
        GitHubPullRequestNumber.DEFAULT.value,
        help="Pull request number in GitHub repository",
    ),
):
    """Comment on a pull request in GitHub repositories."""
    # display the welcome message
    display_welcome_message()
    console.print(
        f":sparkles: Commenting on pull requests in repositories in this GitHub organization: {github_org_url}"
    )
    console.print()
    # extract the usernames from the TOML file
    usernames_parsed = read_usernames_from_json(usernames_file)
    # if there exists a list of usernames only use those usernames as long
    # as they are inside of the parsed usernames, the complete list
    # (i.e., the username variable lets you select a subset of those
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
            "[green]Commenting of Pull Requests", total=len(usernames_parsed)
        )
        # leave a comment on the existing pull
        # request (PR); note that this works because GitHub
        # classroom already creates a PR when the person
        # accepts an assignment. However, it is also possible
        # to specify the PR number on the command line.
        for current_username in usernames_parsed:
            # leave a comment on the existing PR
            # to notify the user of the change
            leave_pr_comment(
                github_org_url,
                repo_prefix,
                current_username,
                None,
                pr_message,
                pr_number,
                token,
                progress,
            )
            # take the next step in the progress bar
            progress.advance(task)


@app.command()
def status(
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
        default=None, help="One or more usernames' accounts to modify"
    ),
):
    """Get the GitHub Actions status for repositories."""
    # create a default console
    # console = Console()
    # display the welcome message
    display_welcome_message()
    console.print(
        f":sparkles: Getting GitHub Actions status for repository: {repo_prefix}-{username}"
    )
    console.print()
    # extract the usernames from the TOML file
    usernames_parsed = read_usernames_from_json(usernames_file)
    # if there exists a list of usernames only use those usernames as long
    # as they are inside of the parsed usernames, the complete list
    # (i.e., the username variable lets you select a subset of those
    # names that are specified in the JSON file of usernames)
    if username:
        usernames_parsed = list(set(username) & set(usernames_parsed))
    # create a progress bar
    with Progress(
        "[progress.description]{task.description}",
        BarColumn(),
        "[progress.percentage]{task.percentage:>3.0f}%",
        TextColumn("[progress.completed]{task.completed}/{task.total}"),
    ) as progress:
        task = progress.add_task(
            "[green]Getting GitHub Actions Status", total=len(usernames_parsed)
        )
        for current_username in usernames_parsed:
            # get the GitHub Actions status
            get_github_actions_status(
                github_org_url,
                repo_prefix,
                current_username,
                token,
                progress,
            )
            # take the next step in the progress bar
            progress.advance(task)


@app.command()
def commit(
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
    directory: Path = typer.Argument(
        ..., help="Directory containing the file(s) to commit"
    ),
    files: List[Path] = typer.Argument(..., help="File(s) to commit"),
    commit_message: str = typer.Argument(
        ..., help="Commit message for the files"
    ),
    destination_directory: Path = typer.Argument(
        ..., help="Destination directory inside the GitHub repository"
    ),
    username: Optional[List[str]] = typer.Option(
        default=None, help="One or more usernames' accounts to modify"
    ),
):
    """Commit files to GitHub repositories."""
    # display the welcome message
    display_welcome_message()
    console.print(
        f":sparkles: Committing files to repositories in this GitHub organization: {github_org_url}"
    )
    console.print()
    # extract the usernames from the JSON file
    usernames_parsed = read_usernames_from_json(usernames_file)
    # if there exists a list of usernames only use those usernames as long
    # as they are inside of the parsed usernames, the complete list
    # (i.e., the username variable lets you select a subset of those
    # names that are specified in the JSON file of usernames)
    if username:
        usernames_parsed = list(set(username) & set(usernames_parsed))
    # create a progress bar
    with Progress(
        "[progress.description]{task.description}",
        BarColumn(),
        "[progress.percentage]{task.percentage:>3.0f}%",
        TextColumn("[progress.completed]{task.completed}/{task.total}"),
    ) as progress:
        task = progress.add_task(
            "[green]Committing Files", total=len(usernames_parsed)
        )
        for current_username in usernames_parsed:
            # commit the files to the repository
            commit_files_to_repo(
                github_org_url,
                repo_prefix,
                current_username,
                token,
                directory,
                files,
                commit_message,
                destination_directory,
                progress,
            )
            # take the next step in the progress bar
            progress.advance(task)
