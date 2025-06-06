"""Determine status of GitHub Actions for GitHub Repositories."""

import requests
from rich.progress import Progress

from reporover.constants import (
    StatusCode,
)
from reporover.util import print_json_string


def get_github_actions_status(
    github_organization_url: str,
    repo_prefix: str,
    username: str,
    token: str,
    progress: Progress,
) -> StatusCode:
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
        # could not find any workflow runs to display, note that this
        # does not correspond to an error because of the fact that
        # it was possible to access the GitHub API and get a response
        else:
            progress.console.print(
                f"? No GitHub Actions runs found for {full_repository_name}"
            )
        # return success status code, to indicate that it was
        # possible to access the GitHub Actions status for
        # this specific GitHub repository
        return StatusCode.WORKING
    # display error message since the request did not work
    else:
        progress.console.print(
            f" Failed to get GitHub Actions status for {full_repository_name}\n"
            f"  Diagnostic: {response.status_code}"
        )
        print_json_string(response.text, progress)
        # return failure status code, to indicate that it was
        # not possible to access the GitHub Actions status for
        # this specific GitHub repository
        return StatusCode.FAILURE
