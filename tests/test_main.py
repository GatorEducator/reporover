"""Test the main module of the reporepo command-line interface."""

# ruff: noqa: PLR2004

from unittest.mock import Mock, patch

import pytest
from rich.console import Console
from rich.progress import Progress
from typer.testing import CliRunner

from reporover.main import (
    GitHubAccessLevel,
    StatusCode,
    app,
    display_welcome_message,
    modify_user_access,
)

runner = CliRunner()


@pytest.fixture
def progress():
    """Create a fixture to set up the Progress object for testing."""
    console = Console()
    progress = Progress(console=console)
    return progress


def test_cli_provides_help_no_error():
    """Ensure that the CLI interface is working as expected when run with --help."""
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "Usage" in result.output


def test_display_welcome_message():
    """Test that display_welcome_message prints the correct content."""
    # mock the console object used in the function
    with patch("reporover.main.console") as mock_console:
        # call the function
        display_welcome_message()
        # verify console.print was called twice
        assert mock_console.print.call_count == 2
        # verify first call was with no arguments (empty line)
        first_call = mock_console.print.call_args_list[0]
        assert first_call[0] == ()
        # verify second call was with the welcome message
        second_call = mock_console.print.call_args_list[1]
        expected_message = ":sparkles: RepoRover manages and analyzes remote GitHub repositories! Arf!"
        assert second_call[0][0] == expected_message


def test_display_welcome_message_console_calls():
    """Test the specific console calls made by display_welcome_message."""
    # mock the console object
    with patch("reporover.main.console") as mock_console:
        # call the function
        display_welcome_message()
        # verify console.print was called exactly twice
        assert mock_console.print.call_count == 2
        # verify first call was with no arguments (empty line)
        first_call_args = mock_console.print.call_args_list[0][0]
        assert first_call_args == ()
        # verify second call was with the welcome message
        second_call_args = mock_console.print.call_args_list[1][0]
        expected_message = ":sparkles: RepoRover manages and analyzes remote GitHub repositories! Arf!"
        assert len(second_call_args) == 1
        assert second_call_args[0] == expected_message


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
