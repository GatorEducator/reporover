"""Test suite for the pull request module."""

import json
from unittest.mock import Mock, patch

import pytest

from reporover.constants import (
    GitHubAccessLevel,
    PullRequestMessages,
    StatusCode,
)
from reporover.pullrequest import leave_pr_comment


@pytest.fixture
def mock_progress():
    """Create a mock Progress object with console."""
    progress = Mock()
    progress.console = Mock()
    return progress


@pytest.fixture
def sample_request_data():
    """Provide sample data for testing."""
    return {
        "github_organization_url": "https://github.com/test-org/repo",
        "repo_prefix": "assignment",
        "username": "testuser",
        "access_level": GitHubAccessLevel.READ,
        "message": "Please check your repository.",
        "pr_number": 1,
        "token": "test_token_123",
    }


def test_leave_pr_comment_success_with_access_level(
    mock_progress, sample_request_data
):
    """Test successful PR comment with access level specified."""
    # create mock response
    mock_response = Mock()
    mock_response.status_code = StatusCode.CREATED.value
    # create mock POST function
    mock_post = Mock(return_value=mock_response)
    # call the function with patch
    with patch("reporover.pullrequest.requests.post", mock_post):
        leave_pr_comment(
            github_organization_url=sample_request_data[
                "github_organization_url"
            ],
            repo_prefix=sample_request_data["repo_prefix"],
            username=sample_request_data["username"],
            access_level=sample_request_data["access_level"],
            message=sample_request_data["message"],
            pr_number=sample_request_data["pr_number"],
            token=sample_request_data["token"],
            progress=mock_progress,
        )
    # verify the API call was made correctly
    expected_url = "https://api.github.com/repos/test-org/assignment-testuser/issues/1/comments"
    expected_headers = {
        "Authorization": "token test_token_123",
        "Accept": "application/vnd.github.v3+json",
    }
    expected_message = (
        f"Hello @testuser! {PullRequestMessages.MODIFIED_TO_PHRASE.value} `read`. "
        f"{PullRequestMessages.ASSISTANCE_SENTENCE.value} Please check your repository."
    )
    expected_data = {"body": expected_message}
    mock_post.assert_called_once_with(
        expected_url, headers=expected_headers, json=expected_data
    )
    # verify success message was printed
    mock_progress.console.print.assert_called_once()
    success_message = mock_progress.console.print.call_args[0][0]
    assert (
        "Commented on the pull request number 1 for GitHub repository assignment-testuser"
        in success_message
    )


def test_leave_pr_comment_success_without_access_level(
    mock_progress, sample_request_data
):
    """Test successful PR comment without access level specified."""
    # create mock response
    mock_response = Mock()
    mock_response.status_code = StatusCode.CREATED.value
    # create mock POST function
    mock_post = Mock(return_value=mock_response)
    # call the function with patch and no access level
    with patch("reporover.pullrequest.requests.post", mock_post):
        leave_pr_comment(
            github_organization_url=sample_request_data[
                "github_organization_url"
            ],
            repo_prefix=sample_request_data["repo_prefix"],
            username=sample_request_data["username"],
            access_level=None,
            message=sample_request_data["message"],
            pr_number=sample_request_data["pr_number"],
            token=sample_request_data["token"],
            progress=mock_progress,
        )
    # verify the API call was made correctly
    expected_url = "https://api.github.com/repos/test-org/assignment-testuser/issues/1/comments"
    expected_message = "Hello @testuser! Please check your repository."
    expected_data = {"body": expected_message}
    call_args = mock_post.call_args
    # verify the URL was called correctly
    assert call_args[0][0] == expected_url
    # verify the JSON data was sent correctly
    assert call_args[1]["json"] == expected_data
    # verify success message was printed
    mock_progress.console.print.assert_called_once()
    success_message = mock_progress.console.print.call_args[0][0]
    assert (
        "Commented on the pull request number 1 for GitHub repository assignment-testuser"
        in success_message
    )


def test_leave_pr_comment_failure(mock_progress, sample_request_data):
    """Test failed PR comment creation."""
    # create mock response for failure
    mock_response = Mock()
    mock_response.status_code = StatusCode.NOT_FOUND.value
    mock_response.text = json.dumps({"message": "Not Found"})
    # create mock POST function
    mock_post = Mock(return_value=mock_response)
    # mock the print_json_string function
    with patch("reporover.pullrequest.print_json_string") as mock_print_json:
        with patch("reporover.pullrequest.requests.post", mock_post):
            leave_pr_comment(
                github_organization_url=sample_request_data[
                    "github_organization_url"
                ],
                repo_prefix=sample_request_data["repo_prefix"],
                username=sample_request_data["username"],
                access_level=sample_request_data["access_level"],
                message=sample_request_data["message"],
                pr_number=sample_request_data["pr_number"],
                token=sample_request_data["token"],
                progress=mock_progress,
            )
    # verify error message was printed
    mock_progress.console.print.assert_called_once()
    error_message = mock_progress.console.print.call_args[0][0]
    assert (
        "Failed to comment on pull request 1 for GitHub repository assignment-testuser"
        in error_message
    )
    assert "Diagnostic: 404" in error_message
    # verify print_json_string was called with response text
    mock_print_json.assert_called_once_with(
        '{"message": "Not Found"}', mock_progress
    )


def test_leave_pr_comment_different_access_levels(
    mock_progress, sample_request_data
):
    """Test PR comment with different access levels."""
    access_levels = [
        GitHubAccessLevel.READ,
        GitHubAccessLevel.WRITE,
        GitHubAccessLevel.ADMIN,
        GitHubAccessLevel.TRIAGE,
        GitHubAccessLevel.MAINTAIN,
    ]
    for access_level in access_levels:
        # create mock response
        mock_response = Mock()
        mock_response.status_code = StatusCode.CREATED.value
        # create mock POST function
        mock_post = Mock(return_value=mock_response)
        # call the function with patch
        with patch("reporover.pullrequest.requests.post", mock_post):
            leave_pr_comment(
                github_organization_url=sample_request_data[
                    "github_organization_url"
                ],
                repo_prefix=sample_request_data["repo_prefix"],
                username=sample_request_data["username"],
                access_level=access_level,
                message=sample_request_data["message"],
                pr_number=sample_request_data["pr_number"],
                token=sample_request_data["token"],
                progress=mock_progress,
            )
        # verify correct access level was included in message
        call_args = mock_post.call_args
        message_body = call_args[1]["json"]["body"]
        assert f"`{access_level.value}`" in message_body


def test_leave_pr_comment_url_parsing(mock_progress):
    """Test proper URL parsing for different organization URLs."""
    test_cases = [
        {
            "url": "https://github.com/allegheny-college/repo",
            "expected_org": "allegheny-college",
        },
        {
            "url": "https://github.com/test-org-name/some-repo",
            "expected_org": "test-org-name",
        },
        {
            "url": "https://github.com/user123/project",
            "expected_org": "user123",
        },
    ]
    for case in test_cases:
        # create mock response
        mock_response = Mock()
        mock_response.status_code = StatusCode.CREATED.value
        # create mock POST function
        mock_post = Mock(return_value=mock_response)
        # call the function with patch
        with patch("reporover.pullrequest.requests.post", mock_post):
            leave_pr_comment(
                github_organization_url=case["url"],
                repo_prefix="hw",
                username="student",
                access_level=GitHubAccessLevel.READ,
                message="Test message",
                pr_number=2,
                token="token",
                progress=mock_progress,
            )
        # verify correct organization was extracted
        call_args = mock_post.call_args
        expected_url = f"https://api.github.com/repos/{case['expected_org']}/hw-student/issues/2/comments"
        assert call_args[0][0] == expected_url


def test_leave_pr_comment_repository_name_construction(
    mock_progress, sample_request_data
):
    """Test proper repository name construction."""
    test_cases = [
        {
            "prefix": "assignment",
            "username": "john",
            "expected": "assignment-john",
        },
        {
            "prefix": "lab",
            "username": "mary_smith",
            "expected": "lab-mary_smith",
        },
        {
            "prefix": "project1",
            "username": "user123",
            "expected": "project1-user123",
        },
    ]
    for case in test_cases:
        # create mock response
        mock_response = Mock()
        mock_response.status_code = StatusCode.CREATED.value
        # create mock POST function
        mock_post = Mock(return_value=mock_response)
        # call the function with patch
        with patch("reporover.pullrequest.requests.post", mock_post):
            leave_pr_comment(
                github_organization_url=sample_request_data[
                    "github_organization_url"
                ],
                repo_prefix=case["prefix"],
                username=case["username"],
                access_level=GitHubAccessLevel.READ,
                message="Test message",
                pr_number=1,
                token=sample_request_data["token"],
                progress=mock_progress,
            )
        # verify correct repository name in URL
        call_args = mock_post.call_args
        expected_url = f"https://api.github.com/repos/test-org/{case['expected']}/issues/1/comments"
        assert call_args[0][0] == expected_url


def test_leave_pr_comment_headers_and_data(mock_progress, sample_request_data):
    """Test that correct headers and data are sent."""
    # create mock response
    mock_response = Mock()
    mock_response.status_code = StatusCode.CREATED.value
    # create mock POST function
    mock_post = Mock(return_value=mock_response)
    # call the function with patch
    with patch("reporover.pullrequest.requests.post", mock_post):
        leave_pr_comment(
            github_organization_url=sample_request_data[
                "github_organization_url"
            ],
            repo_prefix=sample_request_data["repo_prefix"],
            username=sample_request_data["username"],
            access_level=GitHubAccessLevel.WRITE,
            message="Custom message here",
            pr_number=3,
            token="custom_token_456",
            progress=mock_progress,
        )
    # verify headers
    call_args = mock_post.call_args
    headers = call_args[1]["headers"]
    assert headers["Authorization"] == "token custom_token_456"
    assert headers["Accept"] == "application/vnd.github.v3+json"
    # verify data contains expected message components
    data = call_args[1]["json"]
    expected_message = (
        f"Hello @testuser! {PullRequestMessages.MODIFIED_TO_PHRASE.value} `write`. "
        f"{PullRequestMessages.ASSISTANCE_SENTENCE.value} Custom message here"
    )
    assert data["body"] == expected_message


def test_leave_pr_comment_different_pr_numbers(
    mock_progress, sample_request_data
):
    """Test PR comment with different pull request numbers."""
    pr_numbers = [1, 2, 3, 5, 10]
    for pr_number in pr_numbers:
        # create mock response
        mock_response = Mock()
        mock_response.status_code = StatusCode.CREATED.value
        # create mock POST function
        mock_post = Mock(return_value=mock_response)
        # call the function with patch
        with patch("reporover.pullrequest.requests.post", mock_post):
            leave_pr_comment(
                github_organization_url=sample_request_data[
                    "github_organization_url"
                ],
                repo_prefix=sample_request_data["repo_prefix"],
                username=sample_request_data["username"],
                access_level=GitHubAccessLevel.READ,
                message="Test message",
                pr_number=pr_number,
                token=sample_request_data["token"],
                progress=mock_progress,
            )
        # verify correct PR number in URL
        call_args = mock_post.call_args
        expected_url = f"https://api.github.com/repos/test-org/assignment-testuser/issues/{pr_number}/comments"
        assert call_args[0][0] == expected_url
        # verify success message contains correct PR number
        success_message = mock_progress.console.print.call_args[0][0]
        assert f"pull request number {pr_number}" in success_message


def test_leave_pr_comment_various_status_codes(
    mock_progress, sample_request_data
):
    """Test handling of various HTTP status codes."""
    status_codes = [
        StatusCode.BAD_REQUEST.value,
        StatusCode.UNAUTHORIZED.value,
        StatusCode.FORBIDDEN.value,
        StatusCode.NOT_FOUND.value,
        StatusCode.UNPROCESSABLE_ENTITY.value,
        StatusCode.INTERNAL_SERVER_ERROR.value,
    ]
    for status_code in status_codes:
        # create mock response
        mock_response = Mock()
        mock_response.status_code = status_code
        mock_response.text = json.dumps({"error": f"Status {status_code}"})
        # create mock POST function
        mock_post = Mock(return_value=mock_response)
        # mock the print_json_string function
        with patch("reporover.pullrequest.print_json_string"):
            with patch("reporover.pullrequest.requests.post", mock_post):
                leave_pr_comment(
                    github_organization_url=sample_request_data[
                        "github_organization_url"
                    ],
                    repo_prefix=sample_request_data["repo_prefix"],
                    username=sample_request_data["username"],
                    access_level=sample_request_data["access_level"],
                    message=sample_request_data["message"],
                    pr_number=sample_request_data["pr_number"],
                    token=sample_request_data["token"],
                    progress=mock_progress,
                )
        # verify error message contains status code
        error_message = mock_progress.console.print.call_args[0][0]
        assert f"Diagnostic: {status_code}" in error_message


def test_leave_pr_comment_message_formatting_with_access_level(
    mock_progress, sample_request_data
):
    """Test proper message formatting when access level is provided."""
    # create mock response
    mock_response = Mock()
    mock_response.status_code = StatusCode.CREATED.value
    # create mock POST function
    mock_post = Mock(return_value=mock_response)
    # call the function with patch
    with patch("reporover.pullrequest.requests.post", mock_post):
        leave_pr_comment(
            github_organization_url=sample_request_data[
                "github_organization_url"
            ],
            repo_prefix=sample_request_data["repo_prefix"],
            username="alice",
            access_level=GitHubAccessLevel.ADMIN,
            message="Your work looks great!",
            pr_number=1,
            token=sample_request_data["token"],
            progress=mock_progress,
        )
    # verify message formatting
    call_args = mock_post.call_args
    message_body = call_args[1]["json"]["body"]
    expected_parts = [
        "Hello @alice!",
        PullRequestMessages.MODIFIED_TO_PHRASE.value,
        "`admin`",
        PullRequestMessages.ASSISTANCE_SENTENCE.value,
        "Your work looks great!",
    ]
    for part in expected_parts:
        assert part in message_body


def test_leave_pr_comment_message_formatting_without_access_level(
    mock_progress, sample_request_data
):
    """Test proper message formatting when no access level is provided."""
    # create mock response
    mock_response = Mock()
    mock_response.status_code = StatusCode.CREATED.value
    # create mock POST function
    mock_post = Mock(return_value=mock_response)
    # call the function with patch
    with patch("reporover.pullrequest.requests.post", mock_post):
        leave_pr_comment(
            github_organization_url=sample_request_data[
                "github_organization_url"
            ],
            repo_prefix=sample_request_data["repo_prefix"],
            username="bob",
            access_level=None,
            message="Please review the feedback.",
            pr_number=1,
            token=sample_request_data["token"],
            progress=mock_progress,
        )
    # verify message formatting
    call_args = mock_post.call_args
    message_body = call_args[1]["json"]["body"]
    expected_message = "Hello @bob! Please review the feedback."
    assert message_body == expected_message
    # verify access level phrases are not included
    assert PullRequestMessages.MODIFIED_TO_PHRASE.value not in message_body
    assert PullRequestMessages.ASSISTANCE_SENTENCE.value not in message_body
