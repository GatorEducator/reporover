"""Interact with GitHub repositories."""

import base64
from pathlib import Path
from typing import List

import requests
from git import Repo
from git.exc import GitCommandError
from rich.progress import Progress

from reporover.constants import (
    StatusCode,
)
from reporover.util import print_json_string


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
) -> StatusCode:
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
        try:
            file_content = (directory / file_path).read_bytes()
        except (FileNotFoundError, PermissionError, OSError) as e:
            progress.console.print(
                f" Failed to read file {file_path} from directory {directory}\n"
                f"  Diagnostic: {e!s}"
            )
            return StatusCode.FAILURE
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
            return StatusCode.FAILURE
    return StatusCode.WORKING


def clone_repo_gitpython(  # noqa: PLR0913
    github_organization_url: str,
    repo_prefix: str,
    username: str,
    token: str,
    destination_directory: Path,
    progress: Progress,
) -> StatusCode:
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
        return StatusCode.FAILURE
    try:
        # clone the repository using GitPython
        Repo.clone_from(repo_url, local_path)
        progress.console.print(
            f"󰄬 Cloned {full_repository_name} to {local_path}"
        )
        return StatusCode.WORKING
    except GitCommandError as e:
        progress.console.print(
            f" Failed to clone {full_repository_name}\n  Diagnostic: {e!s}"
        )
        return StatusCode.FAILURE
