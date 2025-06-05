"""Test suite for the GitHub Actions functions in the actions module."""

import json
from unittest.mock import Mock, patch

import pytest

from reporover.actions import get_github_actions_status
from reporover.constants import StatusCode


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
        "token": "test_token_123",
    }


def test_get_github_actions_status_success_with_runs(
    mock_progress, sample_request_data
):
    """Test successful GitHub Actions status retrieval with workflow runs."""
    # create mock response with workflow runs
    mock_response = Mock()
    mock_response.status_code = StatusCode.WORKING.value
    mock_response.json = Mock(
        return_value={
            "workflow_runs": [
                {
                    "status": "completed",
                    "conclusion": "success",
                    "name": "CI",
                    "created_at": "2023-01-01T12:00:00Z",
                }
            ]
        }
    )
    # create mock GET function
    mock_get = Mock(return_value=mock_response)
    # call the function with patch
    with patch("reporover.actions.requests.get", mock_get):
        get_github_actions_status(
            github_organization_url=sample_request_data[
                "github_organization_url"
            ],
            repo_prefix=sample_request_data["repo_prefix"],
            username=sample_request_data["username"],
            token=sample_request_data["token"],
            progress=mock_progress,
        )
    # verify the API call was made correctly
    expected_url = "https://api.github.com/repos/test-org/assignment-testuser/actions/runs"
    expected_headers = {
        "Authorization": "token test_token_123",
        "Accept": "application/vnd.github.v3+json",
    }
    mock_get.assert_called_once_with(expected_url, headers=expected_headers)
    # verify success message was printed
    mock_progress.console.print.assert_called_once()
    success_message = mock_progress.console.print.call_args[0][0]
    assert (
        "Latest GitHub Actions run for assignment-testuser" in success_message
    )
    assert "Status: completed" in success_message
    assert "Conclusion: success" in success_message


def test_get_github_actions_status_no_runs(mock_progress, sample_request_data):
    """Test GitHub Actions status retrieval with no workflow runs."""
    # create mock response with no workflow runs
    mock_response = Mock()
    mock_response.status_code = StatusCode.WORKING.value
    mock_response.json = Mock(return_value={"workflow_runs": []})
    # create mock GET function
    mock_get = Mock(return_value=mock_response)
    # call the function with patch
    with patch("reporover.actions.requests.get", mock_get):
        get_github_actions_status(
            github_organization_url=sample_request_data[
                "github_organization_url"
            ],
            repo_prefix=sample_request_data["repo_prefix"],
            username=sample_request_data["username"],
            token=sample_request_data["token"],
            progress=mock_progress,
        )
    # verify message for no runs was printed
    mock_progress.console.print.assert_called_once()
    message = mock_progress.console.print.call_args[0][0]
    assert "No GitHub Actions runs found for assignment-testuser" in message


def test_get_github_actions_status_failure(mock_progress, sample_request_data):
    """Test failed GitHub Actions status retrieval."""
    # create mock response for failure
    mock_response = Mock()
    mock_response.status_code = StatusCode.NOT_FOUND.value
    mock_response.text = json.dumps({"message": "Not Found"})
    # create mock GET function
    mock_get = Mock(return_value=mock_response)
    # mock the print_json_string function
    with patch("reporover.actions.print_json_string") as mock_print_json:
        with patch("reporover.actions.requests.get", mock_get):
            get_github_actions_status(
                github_organization_url=sample_request_data[
                    "github_organization_url"
                ],
                repo_prefix=sample_request_data["repo_prefix"],
                username=sample_request_data["username"],
                token=sample_request_data["token"],
                progress=mock_progress,
            )
    # verify error message was printed
    mock_progress.console.print.assert_called_once()
    error_message = mock_progress.console.print.call_args[0][0]
    assert (
        "Failed to get GitHub Actions status for assignment-testuser"
        in error_message
    )
    assert "Diagnostic: 404" in error_message
    # verify print_json_string was called with response text
    mock_print_json.assert_called_once_with(
        '{"message": "Not Found"}', mock_progress
    )


def test_get_github_actions_status_url_parsing(mock_progress):
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
        mock_response.status_code = StatusCode.WORKING.value
        mock_response.json = Mock(return_value={"workflow_runs": []})
        # create mock GET function
        mock_get = Mock(return_value=mock_response)
        # call the function with patch
        with patch("reporover.actions.requests.get", mock_get):
            get_github_actions_status(
                github_organization_url=case["url"],
                repo_prefix="hw",
                username="student",
                token="token",
                progress=mock_progress,
            )
        # verify correct organization was extracted
        call_args = mock_get.call_args
        expected_url = f"https://api.github.com/repos/{case['expected_org']}/hw-student/actions/runs"
        assert call_args[0][0] == expected_url


def test_get_github_actions_status_repository_name_construction(
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
        mock_response.status_code = StatusCode.WORKING.value
        mock_response.json = Mock(return_value={"workflow_runs": []})
        # create mock GET function
        mock_get = Mock(return_value=mock_response)
        # call the function with patch
        with patch("reporover.actions.requests.get", mock_get):
            get_github_actions_status(
                github_organization_url=sample_request_data[
                    "github_organization_url"
                ],
                repo_prefix=case["prefix"],
                username=case["username"],
                token=sample_request_data["token"],
                progress=mock_progress,
            )
        # verify correct repository name in URL
        call_args = mock_get.call_args
        expected_url = f"https://api.github.com/repos/test-org/{case['expected']}/actions/runs"
        assert call_args[0][0] == expected_url


def test_get_github_actions_status_various_status_codes(
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
        # create mock GET function
        mock_get = Mock(return_value=mock_response)
        # mock the print_json_string function
        with patch("reporover.actions.print_json_string"):
            with patch("reporover.actions.requests.get", mock_get):
                get_github_actions_status(
                    github_organization_url=sample_request_data[
                        "github_organization_url"
                    ],
                    repo_prefix=sample_request_data["repo_prefix"],
                    username=sample_request_data["username"],
                    token=sample_request_data["token"],
                    progress=mock_progress,
                )
        # verify error message contains status code
        error_message = mock_progress.console.print.call_args[0][0]
        assert f"Diagnostic: {status_code}" in error_message
