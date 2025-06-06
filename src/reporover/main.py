"""Main module for the reporover command-line interface."""

from pathlib import Path
from typing import List, Optional

import requests
import typer
from rich.console import Console
from rich.progress import BarColumn, Progress, TextColumn
from typer import Typer

from reporover.actions import get_github_actions_status
from reporover.constants import (
    GitHubAccessLevel,
    GitHubPullRequestNumber,
    StatusCode,
)
from reporover.pullrequest import leave_pr_comment
from reporover.repository import clone_repo_gitpython, commit_files_to_repo
from reporover.status import get_status_from_codes
from reporover.user import modify_user_access
from reporover.util import read_usernames_from_json

# define the Typer app that will be used
# to run the Typer-based command-line interface
app = Typer()

# create a default console
console = Console()


def display_welcome_message() -> None:
    """Display the welcome message for all reporover commands."""
    console.print()
    console.print(
        ":sparkles: RepoRover manages and analyzes remote GitHub repositories! Arf!"
    )


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
    # extract the usernames from the JSON file
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
        # create a list to keep track of the status codes
        # returned across each of the following iterations
        status_codes: List[List[StatusCode]] = []  # type: ignore[arg-type]
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
            modify_user_status_code = modify_user_access(
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
            leave_pr_comment_status_code = leave_pr_comment(
                github_org_url,
                repo_prefix,
                current_username,
                access_level,
                pr_message,
                pr_number,
                token,
                progress,
            )
            # add the status code to the list
            # as a list of two status code values;
            # the first one is the status code from the
            # modify_user_access function and the
            # second one is the status code from the
            # leave_pr_comment function
            status_codes.append(
                [modify_user_status_code, leave_pr_comment_status_code]
            )
            # take the next step in the progress bar
            progress.advance(task)
    # determine if there was at least one error
    # in the status codes list, which would designate
    # that there was an overall failure in this command
    overall_failure = get_status_from_codes(status_codes)  # type: ignore[arg-type]
    # if there was an overall failure then return a non-zero exit code
    # to indicate that the command did not complete successfully
    if overall_failure:
        progress.console.print(
            f"\n Failed to change at least one access level to '{access_level.value}' in"
            + f" {github_org_url}"
        )
        raise typer.Exit(code=1)


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
        # create a list to keep track of the status codes
        status_codes = []
        # leave a comment on the existing pull
        # request (PR); note that this works because GitHub
        # classroom already creates a PR when the person
        # accepts an assignment. However, it is also possible
        # to specify the PR number on the command line.
        for current_username in usernames_parsed:
            # leave a comment on the existing PR
            # to notify the user of the change
            leave_pr_comment_status_code = leave_pr_comment(
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
            # store the status code for this iteration
            status_codes.append([leave_pr_comment_status_code])
    # determine if there was at least one error
    # in the status codes list, which would designate
    # that there was an overall failure in this command
    overall_failure = get_status_from_codes(status_codes)
    # if there was an overall failure then return a non-zero exit code
    # to indicate that the command did not complete successfully
    if overall_failure:
        progress.console.print(
            "\n Failed to comment on at least one pull request of a repository in"
            + f" {github_org_url}"
        )
        raise typer.Exit(code=1)


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
        f":sparkles: Retrieving GitHub Actions status for repositories in this organization: {github_org_url}"
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
    # create a progress bar for the GitHub Actions status retrieval
    with Progress(
        "[progress.description]{task.description}",
        BarColumn(),
        "[progress.percentage]{task.percentage:>3.0f}%",
        TextColumn("[progress.completed]{task.completed}/{task.total}"),
    ) as progress:
        task = progress.add_task(
            "[green]Getting GitHub Actions Status", total=len(usernames_parsed)
        )
        # create a list to keep track of the status codes
        status_codes: List[List[StatusCode]] = []  # type: ignore[arg-type]
        # for each username, determine the status of their GitHub Actions
        # build for the repository associated with the user in the
        # specified GitHub organization
        for current_username in usernames_parsed:
            # get the GitHub Actions status, making sure to store
            # the status of the attempt to access the GitHub Actions' status
            access_github_actions_status = get_github_actions_status(
                github_org_url,
                repo_prefix,
                current_username,
                token,
                progress,
            )
            # store the status code for this iteration
            status_codes.append([access_github_actions_status])
            # take the next step in the progress bar
            progress.advance(task)
    # determine if there was at least one error
    # in the status codes list, which would designate
    # that there was an overall failure in this command
    overall_failure = get_status_from_codes(status_codes)  # type: ignore[arg-type]
    # if there was an overall failure then return a non-zero exit code
    # to indicate that the command did not complete successfully
    if overall_failure:
        progress.console.print(
            "\n Failed to access the status of GitHub Actions of at least one repository in"
            + f" {github_org_url}"
        )
        raise typer.Exit(code=1)


@app.command()
def commit(  # noqa: PLR0913
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
        f":sparkles: Committing file(s) to repositories in this GitHub organization: {github_org_url}"
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
        # create a list to keep track of the status codes
        status_codes: List[List[StatusCode]] = []  # type: ignore[arg-type]
        for current_username in usernames_parsed:
            # commit the files to the repository
            commit_status_code = commit_files_to_repo(
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
            # store the status code for this iteration
            status_codes.append([commit_status_code])
            # take the next step in the progress bar
            progress.advance(task)
    # determine if there was at least one error
    # in the status codes list, which would designate
    # that there was an overall failure in this command
    overall_failure = get_status_from_codes(status_codes)  # type: ignore[arg-type]
    # if there was an overall failure then return a non-zero exit code
    # to indicate that the command did not complete successfully
    if overall_failure:
        progress.console.print(
            "\n Failed to commit file(s) to at least one repository in"
            + f" {github_org_url}"
        )
        raise typer.Exit(code=1)


@app.command()
def clone(  # noqa: PLR0913
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
    destination_directory: Path = typer.Argument(
        ..., help="Local directory to clone repositories into"
    ),
    username: Optional[List[str]] = typer.Option(
        default=None, help="One or more usernames' accounts to clone"
    ),
):
    """Clone GitHub repositories to a local directory."""
    # display the welcome message
    display_welcome_message()
    console.print(
        f":sparkles: Cloning repositories from this GitHub organization: {github_org_url}"
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
            "[green]Cloning Repositories", total=len(usernames_parsed)
        )
        for current_username in usernames_parsed:
            # clone the repository
            clone_repo_gitpython(
                github_org_url,
                repo_prefix,
                current_username,
                token,
                destination_directory,
                progress,
            )
            # take the next step in the progress bar
            progress.advance(task)
