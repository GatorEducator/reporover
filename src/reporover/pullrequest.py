"""Manage pull requests."""

from typing import Union

import requests
from rich.progress import Progress

from reporover.constants import (
    GitHubAccessLevel,
    PullRequestMessages,
    StatusCode,
)
from reporover.util import print_json_string


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
