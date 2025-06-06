"""Test suite for the repository module."""

# ruff: noqa: PLR2004

import base64
import json
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from reporover.constants import StatusCode
from reporover.repository import commit_files_to_repo


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
        "directory": Path("/tmp/source"),
        "files": [Path("test.txt"), Path("main.py")],
        "commit_message": "Initial commit",
        "destination_directory": Path("src"),
    }


@pytest.fixture
def mock_file_content():
    """Provide mock file content for testing."""
    return b"test file content"


def test_commit_files_to_repo_success_new_files(
    mock_progress, sample_request_data, mock_file_content
):
    """Test successful file commit for new files."""
    # create mock responses
    mock_get_response = Mock()
    mock_get_response.status_code = StatusCode.NOT_FOUND.value
    mock_put_response = Mock()
    mock_put_response.status_code = StatusCode.CREATED.value
    # create mock functions
    mock_get = Mock(return_value=mock_get_response)
    mock_put = Mock(return_value=mock_put_response)
    # mock file reading
    with patch("pathlib.Path.read_bytes", return_value=mock_file_content):
        with patch("reporover.repository.requests.get", mock_get):
            with patch("reporover.repository.requests.put", mock_put):
                commit_files_to_repo(
                    github_organization_url=sample_request_data[
                        "github_organization_url"
                    ],
                    repo_prefix=sample_request_data["repo_prefix"],
                    username=sample_request_data["username"],
                    token=sample_request_data["token"],
                    directory=sample_request_data["directory"],
                    files=sample_request_data["files"],
                    commit_message=sample_request_data["commit_message"],
                    destination_directory=sample_request_data[
                        "destination_directory"
                    ],
                    progress=mock_progress,
                )
    # verify API calls were made correctly
    assert mock_get.call_count == 2
    assert mock_put.call_count == 2
    # verify success messages were printed
    assert mock_progress.console.print.call_count == 2
    success_messages = [
        call[0][0] for call in mock_progress.console.print.call_args_list
    ]
    assert "Committed test.txt to assignment-testuser" in success_messages[0]
    assert "Committed main.py to assignment-testuser" in success_messages[1]


def test_commit_files_to_repo_success_existing_files(
    mock_progress, sample_request_data, mock_file_content
):
    """Test successful file commit for existing files."""
    # create mock responses for existing files
    mock_get_response = Mock()
    mock_get_response.status_code = StatusCode.WORKING.value
    mock_get_response.json.return_value = {"sha": "abc123"}
    mock_put_response = Mock()
    mock_put_response.status_code = StatusCode.WORKING.value
    # create mock functions
    mock_get = Mock(return_value=mock_get_response)
    mock_put = Mock(return_value=mock_put_response)
    # mock file reading
    with patch("pathlib.Path.read_bytes", return_value=mock_file_content):
        with patch("reporover.repository.requests.get", mock_get):
            with patch("reporover.repository.requests.put", mock_put):
                commit_files_to_repo(
                    github_organization_url=sample_request_data[
                        "github_organization_url"
                    ],
                    repo_prefix=sample_request_data["repo_prefix"],
                    username=sample_request_data["username"],
                    token=sample_request_data["token"],
                    directory=sample_request_data["directory"],
                    files=sample_request_data["files"],
                    commit_message=sample_request_data["commit_message"],
                    destination_directory=sample_request_data[
                        "destination_directory"
                    ],
                    progress=mock_progress,
                )
    # verify PUT requests included SHA for existing files
    put_calls = mock_put.call_args_list
    for call in put_calls:
        json_data = call[1]["json"]
        assert "sha" in json_data
        assert json_data["sha"] == "abc123"


def test_commit_files_to_repo_failure(
    mock_progress, sample_request_data, mock_file_content
):
    """Test failed file commit."""
    # create mock responses for failure
    mock_get_response = Mock()
    mock_get_response.status_code = StatusCode.NOT_FOUND.value
    mock_put_response = Mock()
    mock_put_response.status_code = StatusCode.FORBIDDEN.value
    mock_put_response.text = json.dumps({"message": "Forbidden"})
    # create mock functions
    mock_get = Mock(return_value=mock_get_response)
    mock_put = Mock(return_value=mock_put_response)
    # mock file reading and print_json_string
    with patch("pathlib.Path.read_bytes", return_value=mock_file_content):
        with patch(
            "reporover.repository.print_json_string"
        ) as mock_print_json:
            with patch("reporover.repository.requests.get", mock_get):
                with patch("reporover.repository.requests.put", mock_put):
                    commit_files_to_repo(
                        github_organization_url=sample_request_data[
                            "github_organization_url"
                        ],
                        repo_prefix=sample_request_data["repo_prefix"],
                        username=sample_request_data["username"],
                        token=sample_request_data["token"],
                        directory=sample_request_data["directory"],
                        files=sample_request_data["files"],
                        commit_message=sample_request_data["commit_message"],
                        destination_directory=sample_request_data[
                            "destination_directory"
                        ],
                        progress=mock_progress,
                    )
    # verify error messages were printed
    error_messages = [
        call[0][0] for call in mock_progress.console.print.call_args_list
    ]
    assert all("Failed to commit" in msg for msg in error_messages)
    assert all("Diagnostic: 403" in msg for msg in error_messages)
    # verify print_json_string was called
    assert mock_print_json.call_count == 2


def test_commit_files_to_repo_url_parsing(mock_progress, mock_file_content):
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
        # create mock responses
        mock_get_response = Mock()
        mock_get_response.status_code = StatusCode.NOT_FOUND.value
        mock_put_response = Mock()
        mock_put_response.status_code = StatusCode.CREATED.value
        # create mock functions
        mock_get = Mock(return_value=mock_get_response)
        mock_put = Mock(return_value=mock_put_response)
        # mock file reading
        with patch("pathlib.Path.read_bytes", return_value=mock_file_content):
            with patch("reporover.repository.requests.get", mock_get):
                with patch("reporover.repository.requests.put", mock_put):
                    commit_files_to_repo(
                        github_organization_url=case["url"],
                        repo_prefix="hw",
                        username="student",
                        token="token",
                        directory=Path("/tmp"),
                        files=[Path("test.txt")],
                        commit_message="Test commit",
                        destination_directory=Path("src"),
                        progress=mock_progress,
                    )
        # verify correct organization was used in API URLs
        get_call_args = mock_get.call_args
        put_call_args = mock_put.call_args
        expected_base_url = f"https://api.github.com/repos/{case['expected_org']}/hw-student/contents/"
        assert expected_base_url in get_call_args[0][0]
        assert expected_base_url in put_call_args[0][0]


def test_commit_files_to_repo_repository_name_construction(
    mock_progress, mock_file_content
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
        # create mock responses
        mock_get_response = Mock()
        mock_get_response.status_code = StatusCode.NOT_FOUND.value
        mock_put_response = Mock()
        mock_put_response.status_code = StatusCode.CREATED.value
        # create mock functions
        mock_get = Mock(return_value=mock_get_response)
        mock_put = Mock(return_value=mock_put_response)
        # mock file reading
        with patch("pathlib.Path.read_bytes", return_value=mock_file_content):
            with patch("reporover.repository.requests.get", mock_get):
                with patch("reporover.repository.requests.put", mock_put):
                    commit_files_to_repo(
                        github_organization_url="https://github.com/test-org/repo",
                        repo_prefix=case["prefix"],
                        username=case["username"],
                        token="token",
                        directory=Path("/tmp"),
                        files=[Path("test.txt")],
                        commit_message="Test commit",
                        destination_directory=Path("src"),
                        progress=mock_progress,
                    )
        # verify correct repository name in URLs
        get_call_args = mock_get.call_args
        put_call_args = mock_put.call_args
        expected_repo_part = f"test-org/{case['expected']}"
        assert expected_repo_part in get_call_args[0][0]
        assert expected_repo_part in put_call_args[0][0]


def test_commit_files_to_repo_file_encoding(
    mock_progress, sample_request_data
):
    """Test proper base64 encoding of file content."""
    test_content = b"Hello, world!\n"
    expected_encoded = base64.b64encode(test_content).decode()
    # create mock responses
    mock_get_response = Mock()
    mock_get_response.status_code = StatusCode.NOT_FOUND.value
    mock_put_response = Mock()
    mock_put_response.status_code = StatusCode.CREATED.value
    # create mock functions
    mock_get = Mock(return_value=mock_get_response)
    mock_put = Mock(return_value=mock_put_response)
    # mock file reading
    with patch("pathlib.Path.read_bytes", return_value=test_content):
        with patch("reporover.repository.requests.get", mock_get):
            with patch("reporover.repository.requests.put", mock_put):
                commit_files_to_repo(
                    github_organization_url=sample_request_data[
                        "github_organization_url"
                    ],
                    repo_prefix=sample_request_data["repo_prefix"],
                    username=sample_request_data["username"],
                    token=sample_request_data["token"],
                    directory=sample_request_data["directory"],
                    files=[Path("test.txt")],
                    commit_message=sample_request_data["commit_message"],
                    destination_directory=sample_request_data[
                        "destination_directory"
                    ],
                    progress=mock_progress,
                )
    # verify correct base64 encoding was used
    put_call_args = mock_put.call_args
    json_data = put_call_args[1]["json"]
    assert json_data["content"] == expected_encoded


def test_commit_files_to_repo_headers_and_data(
    mock_progress, sample_request_data, mock_file_content
):
    """Test that correct headers and data are sent."""
    # create mock responses
    mock_get_response = Mock()
    mock_get_response.status_code = StatusCode.NOT_FOUND.value
    mock_put_response = Mock()
    mock_put_response.status_code = StatusCode.CREATED.value
    # create mock functions
    mock_get = Mock(return_value=mock_get_response)
    mock_put = Mock(return_value=mock_put_response)
    # mock file reading
    with patch("pathlib.Path.read_bytes", return_value=mock_file_content):
        with patch("reporover.repository.requests.get", mock_get):
            with patch("reporover.repository.requests.put", mock_put):
                commit_files_to_repo(
                    github_organization_url=sample_request_data[
                        "github_organization_url"
                    ],
                    repo_prefix=sample_request_data["repo_prefix"],
                    username=sample_request_data["username"],
                    token="custom_token_456",
                    directory=sample_request_data["directory"],
                    files=[Path("test.txt")],
                    commit_message="Custom commit message",
                    destination_directory=sample_request_data[
                        "destination_directory"
                    ],
                    progress=mock_progress,
                )
    # verify headers
    get_call_args = mock_get.call_args
    put_call_args = mock_put.call_args
    expected_headers = {
        "Authorization": "token custom_token_456",
        "Accept": "application/vnd.github.v3+json",
    }
    assert get_call_args[1]["headers"] == expected_headers
    assert put_call_args[1]["headers"] == expected_headers
    # verify PUT data contains expected components
    json_data = put_call_args[1]["json"]
    assert json_data["message"] == "Custom commit message"
    assert json_data["branch"] == "main"
    assert "content" in json_data
    assert "sha" not in json_data  # new file, no sha


def test_commit_files_to_repo_destination_path_construction(
    mock_progress, sample_request_data, mock_file_content
):
    """Test proper destination path construction."""
    # create mock responses
    mock_get_response = Mock()
    mock_get_response.status_code = StatusCode.NOT_FOUND.value
    mock_put_response = Mock()
    mock_put_response.status_code = StatusCode.CREATED.value
    # create mock functions
    mock_get = Mock(return_value=mock_get_response)
    mock_put = Mock(return_value=mock_put_response)
    # mock file reading
    with patch("pathlib.Path.read_bytes", return_value=mock_file_content):
        with patch("reporover.repository.requests.get", mock_get):
            with patch("reporover.repository.requests.put", mock_put):
                commit_files_to_repo(
                    github_organization_url=sample_request_data[
                        "github_organization_url"
                    ],
                    repo_prefix=sample_request_data["repo_prefix"],
                    username=sample_request_data["username"],
                    token=sample_request_data["token"],
                    directory=sample_request_data["directory"],
                    files=[Path("test.txt")],
                    commit_message=sample_request_data["commit_message"],
                    destination_directory=Path("docs/examples"),
                    progress=mock_progress,
                )
    # verify correct destination path in API URLs
    get_call_args = mock_get.call_args
    put_call_args = mock_put.call_args
    expected_path_suffix = "docs/examples/test.txt"
    assert expected_path_suffix in get_call_args[0][0]
    assert expected_path_suffix in put_call_args[0][0]
