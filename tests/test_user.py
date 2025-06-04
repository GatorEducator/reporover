"""Test cases the user module."""

import json
from unittest.mock import Mock, patch

import pytest

from reporover.constants import GitHubAccessLevel, StatusCode
from reporover.user import modify_user_access


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
        "token": "test_token_123",
    }


def test_modify_user_access_success(mock_progress, sample_request_data):
    """Test successful user access modification."""
    # create mock response
    mock_response = Mock()
    mock_response.status_code = StatusCode.SUCCESS.value
    # create mock PUT function
    mock_put = Mock(return_value=mock_response)
    # call the function
    result = modify_user_access(
        github_organization_url=sample_request_data["github_organization_url"],
        repo_prefix=sample_request_data["repo_prefix"],
        username=sample_request_data["username"],
        access_level=sample_request_data["access_level"],
        token=sample_request_data["token"],
        progress=mock_progress,
        put_request_function=mock_put,
    )
    # verify the result
    assert result == StatusCode.SUCCESS
    # verify the API call was made correctly
    expected_url = "https://api.github.com/repos/test-org/assignment-testuser/collaborators/testuser"
    expected_headers = {
        "Authorization": "token test_token_123",
        "Accept": "application/vnd.github.v3+json",
    }
    expected_data = {"permission": "read"}
    mock_put.assert_called_once_with(
        expected_url, headers=expected_headers, json=expected_data
    )
    # verify success message was printed
    mock_progress.console.print.assert_called_once()
    success_message = mock_progress.console.print.call_args[0][0]
    assert (
        "Changed testuser's access to 'read' in assignment-testuser"
        in success_message
    )


def test_modify_user_access_failure(mock_progress, sample_request_data):
    """Test failed user access modification."""
    # create mock response for failure
    mock_response = Mock()
    mock_response.status_code = StatusCode.NOT_FOUND.value
    mock_response.text = json.dumps({"message": "Not Found"})
    # create mock PUT function
    mock_put = Mock(return_value=mock_response)
    # mock the print_json_string function
    with patch("reporover.user.print_json_string") as mock_print_json:
        # call the function
        result = modify_user_access(
            github_organization_url=sample_request_data[
                "github_organization_url"
            ],
            repo_prefix=sample_request_data["repo_prefix"],
            username=sample_request_data["username"],
            access_level=sample_request_data["access_level"],
            token=sample_request_data["token"],
            progress=mock_progress,
            put_request_function=mock_put,
        )
    # verify the result is None (failure case)
    assert result is None
    # verify error message was printed
    mock_progress.console.print.assert_called_once()
    error_message = mock_progress.console.print.call_args[0][0]
    assert (
        "Failed to change testuser's access to 'read' in assignment-testuser"
        in error_message
    )
    assert "Diagnostic: 404" in error_message
    # verify print_json_string was called with response text
    mock_print_json.assert_called_once_with(
        '{"message": "Not Found"}', mock_progress
    )


def test_modify_user_access_different_access_levels(
    mock_progress, sample_request_data
):
    """Test modification with different access levels."""
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
        mock_response.status_code = StatusCode.SUCCESS.value
        # create mock PUT function
        mock_put = Mock(return_value=mock_response)
        # call the function
        result = modify_user_access(
            github_organization_url=sample_request_data[
                "github_organization_url"
            ],
            repo_prefix=sample_request_data["repo_prefix"],
            username=sample_request_data["username"],
            access_level=access_level,
            token=sample_request_data["token"],
            progress=mock_progress,
            put_request_function=mock_put,
        )
        # verify the result
        assert result == StatusCode.SUCCESS
        # verify correct permission was sent
        call_args = mock_put.call_args
        assert call_args[1]["json"]["permission"] == access_level.value


def test_modify_user_access_url_parsing(mock_progress):
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
        mock_response.status_code = StatusCode.SUCCESS.value
        # create mock PUT function
        mock_put = Mock(return_value=mock_response)
        # call the function
        modify_user_access(
            github_organization_url=case["url"],
            repo_prefix="hw",
            username="student",
            access_level=GitHubAccessLevel.READ,
            token="token",
            progress=mock_progress,
            put_request_function=mock_put,
        )
        # verify correct organization was extracted
        call_args = mock_put.call_args
        expected_url = f"https://api.github.com/repos/{case['expected_org']}/hw-student/collaborators/student"
        assert call_args[0][0] == expected_url


def test_modify_user_access_repository_name_construction(
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
        mock_response.status_code = StatusCode.SUCCESS.value
        # create mock PUT function
        mock_put = Mock(return_value=mock_response)
        # call the function
        modify_user_access(
            github_organization_url=sample_request_data[
                "github_organization_url"
            ],
            repo_prefix=case["prefix"],
            username=case["username"],
            access_level=GitHubAccessLevel.READ,
            token=sample_request_data["token"],
            progress=mock_progress,
            put_request_function=mock_put,
        )
        # verify correct repository name in URL
        call_args = mock_put.call_args
        expected_url = f"https://api.github.com/repos/test-org/{case['expected']}/collaborators/{case['username']}"
        assert call_args[0][0] == expected_url


def test_modify_user_access_headers_and_data(
    mock_progress, sample_request_data
):
    """Test that correct headers and data are sent."""
    # create mock response
    mock_response = Mock()
    mock_response.status_code = StatusCode.SUCCESS.value
    # create mock PUT function
    mock_put = Mock(return_value=mock_response)
    # call the function
    modify_user_access(
        github_organization_url=sample_request_data["github_organization_url"],
        repo_prefix=sample_request_data["repo_prefix"],
        username=sample_request_data["username"],
        access_level=GitHubAccessLevel.WRITE,
        token="custom_token_456",
        progress=mock_progress,
        put_request_function=mock_put,
    )
    # verify headers
    call_args = mock_put.call_args
    headers = call_args[1]["headers"]
    assert headers["Authorization"] == "token custom_token_456"
    assert headers["Accept"] == "application/vnd.github.v3+json"
    # verify data
    data = call_args[1]["json"]
    assert data["permission"] == "write"


def test_modify_user_access_various_status_codes(
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
        # create mock PUT function
        mock_put = Mock(return_value=mock_response)
        # mock the print_json_string function
        with patch("reporover.user.print_json_string"):
            # call the function
            result = modify_user_access(
                github_organization_url=sample_request_data[
                    "github_organization_url"
                ],
                repo_prefix=sample_request_data["repo_prefix"],
                username=sample_request_data["username"],
                access_level=sample_request_data["access_level"],
                token=sample_request_data["token"],
                progress=mock_progress,
                put_request_function=mock_put,
            )
        # verify failure result
        assert result is None
        # verify error message contains status code
        error_message = mock_progress.console.print.call_args[0][0]
        assert f"Diagnostic: {status_code}" in error_message
