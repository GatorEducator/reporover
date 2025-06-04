"""Test the main module of the reporepo command-line interface."""

from unittest.mock import Mock

import pytest
from rich.console import Console
from rich.progress import Progress
from typer.testing import CliRunner

from reporover.main import (
    GitHubAccessLevel,
    StatusCode,
    app,
    modify_user_access,
)

runner = CliRunner()


def test_cli_provides_help_no_error():
    """Ensure that the CLI interface is working as expected when run with --help."""
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "Usage" in result.output


@pytest.fixture
def progress():
    """Create a fixture to set up the Progress object for testing."""
    console = Console()
    progress = Progress(console=console)
    return progress


def test_modify_user_access_success(progress, capsys):
    """Test modify_user_access function with a successful response."""
    mock_put = Mock()
    mock_response = Mock()
    mock_response.status_code = StatusCode.SUCCESS.value
    mock_put.return_value = mock_response
    modified_user_access_status = modify_user_access(
        github_organization_url="https://github.com/org",
        repo_prefix="repo",
        username="user",
        access_level=GitHubAccessLevel.READ,
        token="fake_token",
        progress=progress,
        put_request_function=mock_put,
    )
    mock_put.assert_called_once()
    captured = capsys.readouterr()
    assert modified_user_access_status == StatusCode.SUCCESS
    assert "Failed to change user's access" not in captured.out
    assert "󰄬 Changed user's access to" in captured.out.strip()


def test_modify_user_access_failure(progress, capsys):
    """Test modify_user_access function with a failed response."""
    mock_put = Mock()
    mock_response = Mock()
    mock_response.status_code = StatusCode.BAD_REQUEST.value
    mock_response.text = '{"message": "Bad request", "documentation_url": "https://docs.github.com/rest"}'
    mock_put.return_value = mock_response
    modified_user_access_status = modify_user_access(
        github_organization_url="https://github.com/org",
        repo_prefix="repo",
        username="user",
        access_level=GitHubAccessLevel.READ,
        token="fake_token",
        progress=progress,
        put_request_function=mock_put,
    )
    mock_put.assert_called_once()
    captured = capsys.readouterr()
    assert modified_user_access_status is None
    assert captured.out is not None
    assert "Failed to change user's access to" in captured.out
    assert "read" in captured.out
    assert "Diagnostic" in captured.out
    assert "400" in captured.out
    assert "Bad request" in captured.out
    assert "documentation_url" in captured.out
