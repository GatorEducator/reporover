"""Constants for RepoRover."""

from enum import Enum


class Data(Enum):
    """Define the attributes inside of the user data."""

    USERNAMES = "usernames"


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


class StatusCode(Enum):
    """Define the status codes for the GitHub API and an extra code for overall failure."""

    WORKING = 200
    CREATED = 201
    SUCCESS = 204
    BAD_REQUEST = 400
    UNAUTHORIZED = 401
    FORBIDDEN = 403
    NOT_FOUND = 404
    UNPROCESSABLE_ENTITY = 422
    INTERNAL_SERVER_ERROR = 500
    FAILURE = 600
