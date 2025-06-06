"""Main module for the reporover command-line interface."""

import base64
import csv
import json
from datetime import datetime
from pathlib import Path
from typing import List, Optional

import requests
import typer
from git import Repo
from git.exc import GitCommandError
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
from reporover.status import get_status_from_codes
from reporover.user import modify_user_access
from reporover.util import print_json_string, read_usernames_from_json

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
    organization_name = github_organization_url.split("github.com/")[1].split(
        "/"
    )[0]
    full_repository_name = f"{repo_prefix}-{username}"
    full_name_for_api = f"{organization_name}/{full_repository_name}"
    api_url = f"https://api.github.com/repos/{full_name_for_api}/contents/"
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json",
    }
    for file_path in files:
        file_content = (directory / file_path).read_bytes()
        encoded_content = base64.b64encode(file_content).decode()
        destination_path = destination_directory / file_path.name
        get_response = requests.get(
            api_url + destination_path.as_posix(), headers=headers
        )
        if get_response.status_code == StatusCode.WORKING.value:
            sha = get_response.json()["sha"]
            data = {
                "message": commit_message,
                "content": encoded_content,
                "branch": "main",
                "sha": sha,
            }
        else:
            data = {
                "message": commit_message,
                "content": encoded_content,
                "branch": "main",
            }
        response = requests.put(
            api_url + destination_path.as_posix(), headers=headers, json=data
        )
        if response.status_code in [
            StatusCode.WORKING.value,
            StatusCode.CREATED.value,
        ]:
            progress.console.print(
                f"󰄬 Committed {file_path.name} to {full_repository_name} in directory '{destination_directory}'"
            )
        else:
            progress.console.print(
                f" Failed to commit {file_path.name} to {full_repository_name} in directory '{destination_directory}'\n"
                f"  Diagnostic: {response.status_code}"
            )
            print_json_string(response.text, progress)


def clone_repo_gitpython(  # noqa: PLR0913
    github_organization_url: str,
    repo_prefix: str,
    username: str,
    token: str,
    destination_directory: Path,
    progress: Progress,
) -> None:
    """Clone a GitHub repository to a local directory."""
    # extract the organization name from the URL
    organization_name = github_organization_url.split("github.com/")[1].split(
        "/"
    )[0]
    # define the full name of the repository
    full_repository_name = f"{repo_prefix}-{username}"
    # construct the repository URL with authentication token
    repo_url = f"https://{token}@github.com/{organization_name}/{full_repository_name}.git"
    # define the local path for the cloned repository
    local_path = destination_directory / full_repository_name
    # confirm that the local path does not exist
    if local_path.exists():
        progress.console.print(
            f" Failed to clone {full_repository_name} to {local_path}\n"
            f"  Diagnostic: {local_path} already exists"
        )
        return None
    try:
        # clone the repository using GitPython
        Repo.clone_from(repo_url, local_path)
        progress.console.print(
            f"󰄬 Cloned {full_repository_name} to {local_path}"
        )
    except GitCommandError as e:
        progress.console.print(
            f" Failed to clone {full_repository_name}\n  Diagnostic: {e!s}"
        )


def generate_commit_details(  # noqa: PLR0913
    github_organization_url: str,
    repo_prefix: str,
    username: str,
    token: str,
    progress: Progress,
    verbose: bool = False,
) -> List[dict]:
    """Generate commit details for a GitHub repository."""
    # extract the organization name from the URL
    organization_name = github_organization_url.split("github.com/")[1].split(
        "/"
    )[0]
    # define the full name of the repository
    full_repository_name = f"{repo_prefix}-{username}"
    full_name_for_api = f"{organization_name}/{full_repository_name}"
    # define the API URL for the repository commits
    api_url = f"https://api.github.com/repos/{full_name_for_api}/commits"
    # headers for the request
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json",
    }
    # make the GET request to get the repository commits
    response = requests.get(api_url, headers=headers)
    commit_details = []
    # check if the request was successful
    if response.status_code == StatusCode.WORKING.value:
        commits = response.json()
        for commit in commits:
            commit_sha = commit["sha"]
            commit_url = f"{api_url}/{commit_sha}"
            commit_response = requests.get(commit_url, headers=headers)
            if commit_response.status_code == StatusCode.WORKING.value:
                commit_data = commit_response.json()
                commit_info = {
                    "organization_name": organization_name,
                    "repository_name": full_repository_name,
                    "commit_sha": commit_data["sha"],
                    "commit_url": commit_data["html_url"],
                    "commit_message": commit_data["commit"]["message"],
                    "author": commit_data["commit"]["author"]["name"],
                    "author_email": commit_data["commit"]["author"]["email"],
                    "committer": commit_data["commit"]["committer"]["name"],
                    "committer_email": commit_data["commit"]["committer"][
                        "email"
                    ],
                    "date": commit_data["commit"]["author"]["date"],
                    "files_changed": [
                        file["filename"] for file in commit_data["files"]
                    ],
                    "number_files_changed": len(commit_data["files"]),
                    "extensions_files_changed": list(
                        set(
                            file["filename"].split(".")[-1]
                            for file in commit_data["files"]
                        )
                    ),
                    "lines_changed": sum(
                        file["changes"] for file in commit_data["files"]
                    ),
                    "additions": sum(
                        file["additions"] for file in commit_data["files"]
                    ),
                    "deletions": sum(
                        file["deletions"] for file in commit_data["files"]
                    ),
                    "diff": commit_data["html_url"],
                    "parent_commits": [
                        parent["sha"] for parent in commit_data["parents"]
                    ],
                    "verification_status": commit_data["commit"][
                        "verification"
                    ]["verified"],
                    "build_status": "unknown",  # add a placeholder for build status
                }
                # if the verbose flag is set, display the commit details
                if verbose:
                    progress.console.print(f"󰄬 Accessing commit {commit_sha}")
                # check if the commit triggered a build and get the status
                actions_url = f"https://api.github.com/repos/{full_name_for_api}/actions/runs"
                actions_response = requests.get(actions_url, headers=headers)
                # extract the build status for the commit
                if actions_response.status_code == StatusCode.WORKING.value:
                    runs = actions_response.json().get("workflow_runs", [])
                    found_build_status_for_run = False
                    # iterate through all of the runs to find the build status
                    # for the specific commit subject to analysis
                    for run in runs:
                        # found details so record them and then also echo
                        # details to the console if the verbose flag is set
                        if run["head_sha"] == commit_sha:
                            commit_info["build_status"] = run["conclusion"]
                            found_build_status_for_run = True
                            if verbose:
                                progress.console.print(
                                    f"󰄬 Found build status for {commit_sha}"
                                )
                            break
                    # did not find details so echo a message if the verbose flag is set
                    if not found_build_status_for_run:
                        progress.console.print(
                            f"? No build status for {commit_sha}"
                        )
                commit_details.append(commit_info)
        progress.console.print(
            f"󰄬 Retrieved commit details for {full_repository_name}"
        )
    else:
        progress.console.print(
            f" Failed to retrieve commit details for {full_repository_name}\n"
            f"  Diagnostic: {response.status_code}"
        )
        print_json_string(response.text, progress)
    return commit_details


def generate_commit_details_jobs(  # noqa: PLR0912, PLR0913
    github_organization_url: str,
    repo_prefix: str,
    username: str,
    token: str,
    progress: Progress,
    verbose: bool,
):
    """Generate commit details for a GitHub repository."""
    # extract the organization name from the URL
    organization_name = github_organization_url.split("github.com/")[1].split(
        "/"
    )[0]
    # define the full name of the repository
    full_repository_name = f"{repo_prefix}-{username}"
    full_name_for_api = f"{organization_name}/{full_repository_name}"
    # define the API URL for the repository commits
    api_url = f"https://api.github.com/repos/{full_name_for_api}/commits"
    # headers for the request
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json",
    }
    # make the GET request to get the repository commits
    response = requests.get(api_url, headers=headers)
    commit_details = []
    # check if the request was successful
    if response.status_code == StatusCode.WORKING.value:
        commits = response.json()
        for commit in commits:
            commit_sha = commit["sha"]
            commit_url = f"{api_url}/{commit_sha}"
            commit_response = requests.get(commit_url, headers=headers)
            if commit_response.status_code == StatusCode.WORKING.value:
                commit_data = commit_response.json()
                commit_info = {
                    "organization_name": organization_name,
                    "repository_name": full_repository_name,
                    "commit_sha": commit_data["sha"],
                    "commit_url": commit_data["html_url"],
                    "commit_message": commit_data["commit"]["message"],
                    "author": commit_data["commit"]["author"]["name"],
                    "author_email": commit_data["commit"]["author"]["email"],
                    "committer": commit_data["commit"]["committer"]["name"],
                    "committer_email": commit_data["commit"]["committer"][
                        "email"
                    ],
                    "date": commit_data["commit"]["author"]["date"],
                    "files_changed": [
                        file["filename"] for file in commit_data["files"]
                    ],
                    "number_files_changed": len(commit_data["files"]),
                    "extensions_files_changed": list(
                        set(
                            file["filename"].split(".")[-1]
                            for file in commit_data["files"]
                        )
                    ),
                    "lines_changed": sum(
                        file["changes"] for file in commit_data["files"]
                    ),
                    "additions": sum(
                        file["additions"] for file in commit_data["files"]
                    ),
                    "deletions": sum(
                        file["deletions"] for file in commit_data["files"]
                    ),
                    "diff": commit_data["html_url"],
                    "parent_commits": [
                        parent["sha"] for parent in commit_data["parents"]
                    ],
                    "verification_status": commit_data["commit"][
                        "verification"
                    ]["verified"],
                    "build_status": "unknown",  # add a placeholder for build status
                }
                # if the verbose flag is set, display the commit details
                if verbose:
                    progress.console.print(f"󰄬 Accessing commit {commit_sha}")
                # check if the commit triggered a build and get the status
                actions_url = f"https://api.github.com/repos/{full_name_for_api}/actions/runs"
                actions_response = requests.get(actions_url, headers=headers)
                # extract the build status for the commit
                if actions_response.status_code == StatusCode.WORKING.value:
                    runs = actions_response.json().get("workflow_runs", [])
                    found_build_status_for_run = False
                    # iterate through all of the runs to find the build status
                    # for the specific commit subject to analysis
                    for run in runs:
                        # found details so record them and then also echo
                        # details to the console if the verbose flag is set
                        if run["head_sha"] == commit_sha:
                            commit_info["build_status"] = run["conclusion"]
                            found_build_status_for_run = True
                            if verbose:
                                progress.console.print(
                                    f"󰄬 Found build status for {commit_sha}"
                                )
                            # collect details about the steps in the final workflow run
                            steps_url = f"https://api.github.com/repos/{full_name_for_api}/actions/runs/{run['id']}/jobs"
                            steps_response = requests.get(
                                steps_url, headers=headers
                            )
                            if (
                                steps_response.status_code
                                == StatusCode.WORKING.value
                            ):
                                jobs = steps_response.json().get("jobs", [])
                                if jobs:
                                    final_job = jobs[-1]
                                    commit_info["steps"] = []
                                    for step in final_job["steps"]:
                                        # display the contents of the step
                                        # progress.console.print(step)
                                        step_info = {
                                            "name": step["name"],
                                            "status": step["status"],
                                            "conclusion": step["conclusion"],
                                        }
                                        # Fetch the log for the job
                                        job_id = final_job["id"]
                                        log_url = f"https://api.github.com/repos/{full_name_for_api}/actions/jobs/{job_id}/logs"
                                        log_response = requests.get(
                                            log_url, headers=headers
                                        )
                                        if (
                                            log_response.status_code
                                            == StatusCode.WORKING.value
                                        ):
                                            step_info["log"] = (
                                                log_response.text
                                            )
                                        commit_info["steps"].append(step_info)
                            break
                    # did not find details so echo a message if the verbose flag is set
                    if not found_build_status_for_run:
                        progress.console.print(
                            f"? No build status for {commit_sha}"
                        )
                commit_details.append(commit_info)
        progress.console.print(
            f"󰄬 Retrieved commit details for {full_repository_name}"
        )
    else:
        progress.console.print(
            f" Failed to retrieve commit details for {full_repository_name}\n"
            f"  Diagnostic: {response.status_code}"
        )
        print_json_string(response.text, progress)
    return commit_details


def save_commit_details_to_file(  # noqa: PLR0913
    commit_details: List[dict],
    output_directory: Path,
    github_org_name: str,
    repo_prefix: str,
    file_format: str,
    progress: Progress,
) -> None:
    """Save commit details to a file in the specified format (JSON or CSV)."""
    # generate the file name based on the GitHub organization and the current date;
    # note that this includes the minutes and seconds so as to ensure that this
    # information makes file names different when the reporover is run multiple
    # times within the same minute on the same day
    date_str = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    file_name = f"{github_org_name}_{repo_prefix}_{date_str}.{file_format}"
    file_path = output_directory / file_name
    if file_format == "json":
        # write the commit details to a JSON file
        with file_path.open("w") as jsonfile:
            json.dump(commit_details, jsonfile, indent=4)
        console.print(f"󰄬 Commit details written to {file_path}")
    elif file_format == "csv":
        # write the commit details to a CSV file
        with file_path.open("w", newline="") as csvfile:
            fieldnames = [
                "commit_message",
                "author",
                "date",
                "files_changed",
                "lines_changed",
                "additions",
                "deletions",
                "diff",
                "build_status",
            ]
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            for commit_detail in commit_details:
                writer.writerow(commit_detail)
        progress.console.print(f"󰄬 Commit details written to {file_path}")
    else:
        progress.console.print(f" Unsupported file format: {file_format}")


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


@app.command()
def details(  # noqa: PLR0913
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
    output_directory: Path = typer.Argument(
        ..., help="Directory to save the output file"
    ),
    file_format: str = typer.Argument(
        ..., help="Output file format (json or csv)"
    ),
    username: Optional[List[str]] = typer.Option(
        default=None, help="One or more usernames' accounts to analyze"
    ),
    verbose: bool = typer.Option(default=False, help="Display verbose output"),
):
    """Generate commit details for GitHub repositories and save to a file (JSON or CSV)."""
    # display the welcome message
    display_welcome_message()
    console.print(
        f":sparkles: Generating commit details for repositories in this GitHub organization: {github_org_url}"
    )
    console.print(
        f":sparkles: Analyzing repositories with the following prefix in their name: {repo_prefix}"
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
            "[green]Generating Commit Details", total=len(usernames_parsed)
        )
        all_commit_details = []
        for current_username in usernames_parsed:
            # generate the commit details
            commit_details = generate_commit_details_jobs(
                github_org_url,
                repo_prefix,
                current_username,
                token,
                progress,
                verbose,
            )
            all_commit_details.extend(commit_details)
            # take the next step in the progress bar
            progress.advance(task)
    # save the commit details to the specified file format
    github_org_name = github_org_url.split("github.com/")[1].split("/")[0]
    save_commit_details_to_file(
        all_commit_details,
        output_directory,
        github_org_name,
        repo_prefix,
        file_format,
        progress,
    )
