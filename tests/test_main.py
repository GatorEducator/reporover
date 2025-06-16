"""Test the main module of the reporepo command-line interface."""

# ruff: noqa: PLR2004

from unittest.mock import Mock, patch

import pytest
from rich.console import Console
from rich.progress import Progress
from typer.testing import CliRunner

from reporover.constants import (
    GitHubAccessLevel,
    GitHubPullRequestNumber,
    StatusCode,
)
from reporover.main import (
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


@pytest.fixture
def temp_usernames_file(tmp_path):
    """Create a temporary JSON file with test usernames."""
    import json

    usernames_data = {
        "usernames": ["gkapfham", "student1", "student2", "student3"]
    }
    usernames_file = tmp_path / "github_usernames_test.json"
    usernames_file.write_text(json.dumps(usernames_data))
    return usernames_file


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
    assert modified_user_access_status is StatusCode.FAILURE
    assert captured.out is not None
    assert "Failed to change user's access to" in captured.out
    assert "read" in captured.out
    assert "Diagnostic" in captured.out
    assert "400" in captured.out
    assert "Bad request" in captured.out
    assert "documentation_url" in captured.out


def test_cli_access_command_with_all_parameters_success_read(
    temp_usernames_file,
):
    """Test the access command with all parameters provided for success case."""
    # mock the functions called by the CLI
    with (
        patch("reporover.main.modify_user_access") as mock_modify_user,
        patch("reporover.main.leave_pr_comment") as mock_leave_pr,
    ):
        # configure the mocks to simulate success
        mock_modify_user.return_value = StatusCode.SUCCESS
        # define the command arguments that match the real usage
        result = runner.invoke(
            app,
            [
                "access",
                "https://github.com/Allegheny-Computer-Science-202-S2025/",
                "computer-science-202-algorithm-analysis-executable-exam-3",
                str(temp_usernames_file),
                "github_access_token_fake_1234",
                "--username",
                "gkapfham",
                "--access-level",
                "read",
                "--pr-number",
                "1",
                "--pr-message",
                "Questions? Please check the course web site at: https://www.algorithmology.org for more details or visit https://www.gregorykapfhammer.com/schedule/ to schedule an office hours appointment with the course instructor.",
            ],
        )
        # verify the command executed successfully
        assert result.exit_code == 0
        # verify the mocked functions were called
        mock_modify_user.assert_called()
        mock_leave_pr.assert_called()


def test_cli_access_command_with_all_parameters_success_write():
    """Test the access command with all parameters provided for success case."""
    # mock the functions called by the CLI
    with (
        patch("reporover.main.modify_user_access") as mock_modify_user,
        patch("reporover.main.leave_pr_comment") as mock_leave_pr,
    ):
        # configure the mocks to simulate success
        mock_modify_user.return_value = StatusCode.SUCCESS
        # define the command arguments that match the real usage
        result = runner.invoke(
            app,
            [
                "access",
                "https://github.com/Allegheny-Computer-Science-202-S2025/",
                "computer-science-202-algorithm-analysis-executable-exam-3",
                "/home/gkapfham/working/teaching/github-classroom/algorithmology/github-usernames/github_usernames_spring2025.json",
                "github_access_token_fake_1234",
                "--username",
                "gkapfham",
                "--access-level",
                "write",
                "--pr-number",
                "1",
                "--pr-message",
                "Questions? Please check the course web site at: https://www.algorithmology.org for more details or visit https://www.gregorykapfhammer.com/schedule/ to schedule an office hours appointment with the course instructor.",
            ],
        )
        # verify the command executed successfully
        assert result.exit_code == 0
        # verify the mocked functions were called
        mock_modify_user.assert_called()
        mock_leave_pr.assert_called()


def test_cli_access_command_with_all_parameters_failure():
    """Test the access command with all parameters provided for failure case."""
    # mock the functions called by the CLI
    with (
        patch("reporover.main.modify_user_access") as mock_modify_user,
        patch("reporover.main.leave_pr_comment") as mock_leave_pr,
    ):
        # configure the mocks to simulate failure
        mock_modify_user.return_value = StatusCode.FAILURE
        # define the command arguments that match the real usage
        result = runner.invoke(
            app,
            [
                "access",
                "https://github.com/Allegheny-Computer-Science-202-S2025/",
                "computer-science-202-algorithm-analysis-executable-exam-3",
                "/home/gkapfham/working/teaching/github-classroom/algorithmology/github-usernames/github_usernames_spring2025.json",
                "github_access_token_fake_1234",
                "--username",
                "gkapfham",
                "--access-level",
                "write",
                "--pr-number",
                "1",
                "--pr-message",
                "Questions? Please check the course web site at: https://www.algorithmology.org for more details or visit https://www.gregorykapfhammer.com/schedule/ to schedule an office hours appointment with the course instructor.",
            ],
        )
        # verify the command executed without crashing
        assert result.exit_code == 1
        # verify the modify_user_access function was called
        mock_modify_user.assert_called()
        # verify leave_pr_comment was not called due to the failure
        mock_leave_pr.assert_called()


def test_cli_comment_command_with_all_parameters_success():
    """Test the comment command with all parameters provided for success case."""
    # mock the functions called by the CLI
    with patch("reporover.main.leave_pr_comment") as mock_leave_pr:
        # configure the mocks to simulate success
        mock_leave_pr.return_value = StatusCode.SUCCESS
        # define the command arguments that match the real usage
        result = runner.invoke(
            app,
            [
                "comment",
                "https://github.com/Allegheny-Computer-Science-202-S2025/",
                "computer-science-202-algorithm-analysis-executable-exam-3",
                "/home/gkapfham/working/teaching/github-classroom/algorithmology/github-usernames/github_usernames_spring2025.json",
                "Questions? Please check the course web site at: https://www.algorithmology.org for more details or visit https://www.gregorykapfhammer.com/schedule/ to schedule an office hours appointment with the course instructor.",
                "github_access_token_fake_1234",
                "--username",
                "gkapfham",
                "--pr-number",
                "1",
            ],
        )
        # verify the command executed successfully
        assert result.exit_code == 0
        # verify the mocked function was called
        mock_leave_pr.assert_called()


def test_cli_comment_command_with_all_parameters_failure():
    """Test the comment command with all parameters provided for failure case."""
    # mock the functions called by the CLI
    with patch("reporover.main.leave_pr_comment") as mock_leave_pr:
        # configure the mocks to simulate failure
        mock_leave_pr.return_value = StatusCode.FAILURE
        # define the command arguments that match the real usage
        result = runner.invoke(
            app,
            [
                "comment",
                "https://github.com/Allegheny-Computer-Science-202-S2025/",
                "computer-science-202-algorithm-analysis-executable-exam-3",
                "/home/gkapfham/working/teaching/github-classroom/algorithmology/github-usernames/github_usernames_spring2025.json",
                "Questions? Please check the course web site at: https://www.algorithmology.org for more details or visit https://www.gregorykapfhammer.com/schedule/ to schedule an office hours appointment with the course instructor.",
                "github_access_token_fake_1234",
                "--username",
                "gkapfham",
                "--pr-number",
                "1",
            ],
        )
        # verify the command executed with failure exit code
        assert result.exit_code == 1
        # verify the mocked function was called
        mock_leave_pr.assert_called()


def test_cli_comment_command_multiple_usernames_success():
    """Test the comment command with multiple usernames for success case."""
    # mock the functions called by the CLI
    with patch("reporover.main.leave_pr_comment") as mock_leave_pr:
        # configure the mocks to simulate success
        mock_leave_pr.return_value = StatusCode.SUCCESS
        # define the command arguments with multiple usernames
        result = runner.invoke(
            app,
            [
                "comment",
                "https://github.com/Allegheny-Computer-Science-202-S2025/",
                "computer-science-202-algorithm-analysis-executable-exam-3",
                "/home/gkapfham/working/teaching/github-classroom/algorithmology/github-usernames/github_usernames_spring2025.json",
                "Questions? Please check the course web site at: https://www.algorithmology.org for more details or visit https://www.gregorykapfhammer.com/schedule/ to schedule an office hours appointment with the course instructor.",
                "github_access_token_fake_1234",
                "--username",
                "gkapfham",
                "--username",
                "student1",
                "--pr-number",
                "2",
            ],
        )
        # verify the command executed successfully
        assert result.exit_code == 0
        # verify the mocked function was called multiple times
        assert mock_leave_pr.call_count >= 1


def test_cli_comment_command_default_pr_number():
    """Test the comment command with default PR number."""
    # mock the functions called by the CLI
    with patch("reporover.main.leave_pr_comment") as mock_leave_pr:
        # configure the mocks to simulate success
        mock_leave_pr.return_value = StatusCode.SUCCESS
        # define the command arguments without specifying pr-number
        result = runner.invoke(
            app,
            [
                "comment",
                "https://github.com/Allegheny-Computer-Science-202-S2025/",
                "computer-science-202-algorithm-analysis-executable-exam-3",
                "/home/gkapfham/working/teaching/github-classroom/algorithmology/github-usernames/github_usernames_spring2025.json",
                "Questions? Please check the course web site at: https://www.algorithmology.org for more details or visit https://www.gregorykapfhammer.com/schedule/ to schedule an office hours appointment with the course instructor.",
                "github_access_token_fake_1234",
                "--username",
                "gkapfham",
            ],
        )
        # verify the command executed successfully
        assert result.exit_code == 0
        # verify the mocked function was called with default PR number
        mock_leave_pr.assert_called()
        call_args = mock_leave_pr.call_args
        # check that the pr_number argument (index 5) is the default value
        assert call_args[0][5] == GitHubPullRequestNumber.DEFAULT.value


def test_cli_comment_command_mixed_success_failure():
    """Test the comment command with mixed success and failure results."""
    # mock the functions called by the CLI
    with (
        patch("reporover.main.leave_pr_comment") as mock_leave_pr,
        patch(
            "reporover.main.read_usernames_from_json"
        ) as mock_read_usernames,
    ):
        # configure the mocks to simulate mixed results
        mock_read_usernames.return_value = ["gkapfham", "student1"]
        mock_leave_pr.side_effect = [StatusCode.SUCCESS, StatusCode.FAILURE]
        # define the command arguments with multiple usernames
        result = runner.invoke(
            app,
            [
                "comment",
                "https://github.com/Allegheny-Computer-Science-202-S2025/",
                "computer-science-202-algorithm-analysis-executable-exam-3",
                "/home/gkapfham/working/teaching/github-classroom/algorithmology/github-usernames/github_usernames_spring2025.json",
                "Questions? Please check the course web site at: https://www.algorithmology.org for more details or visit https://www.gregorykapfhammer.com/schedule/ to schedule an office hours appointment with the course instructor.",
                "github_access_token_fake_1234",
                "--username",
                "gkapfham",
                "--username",
                "student1",
            ],
        )
        # verify the command executed with failure exit code due to mixed results
        assert result.exit_code == 1
        # verify the mocked function was called multiple times
        assert mock_leave_pr.call_count == 2


def test_cli_status_command_with_all_parameters_success():
    """Test the status command with all parameters provided for success case."""
    # mock the functions called by the CLI
    with patch("reporover.main.get_github_actions_status") as mock_get_status:
        # configure the mocks to simulate success
        mock_get_status.return_value = StatusCode.SUCCESS
        # define the command arguments that match the real usage
        result = runner.invoke(
            app,
            [
                "status",
                "https://github.com/Allegheny-Computer-Science-202-S2025/",
                "computer-science-202-algorithm-analysis-executable-exam-3",
                "/home/gkapfham/working/teaching/github-classroom/algorithmology/github-usernames/github_usernames_spring2025.json",
                "github_access_token_fake_1234",
                "--username",
                "gkapfham",
            ],
        )
        # verify the command executed successfully
        assert result.exit_code == 0
        # verify the mocked function was called
        mock_get_status.assert_called()


def test_cli_status_command_with_all_parameters_failure():
    """Test the status command with all parameters provided for failure case."""
    # mock the functions called by the CLI
    with patch("reporover.main.get_github_actions_status") as mock_get_status:
        # configure the mocks to simulate failure
        mock_get_status.return_value = StatusCode.FAILURE
        # define the command arguments that match the real usage
        result = runner.invoke(
            app,
            [
                "status",
                "https://github.com/Allegheny-Computer-Science-202-S2025/",
                "computer-science-202-algorithm-analysis-executable-exam-3",
                "/home/gkapfham/working/teaching/github-classroom/algorithmology/github-usernames/github_usernames_spring2025.json",
                "github_access_token_fake_1234",
                "--username",
                "gkapfham",
            ],
        )
        # verify the command executed with failure exit code
        assert result.exit_code == 1
        # verify the mocked function was called
        mock_get_status.assert_called()


def test_cli_status_command_multiple_usernames_success():
    """Test the status command with multiple usernames for success case."""
    # mock the functions called by the CLI
    with patch("reporover.main.get_github_actions_status") as mock_get_status:
        # configure the mocks to simulate success
        mock_get_status.return_value = StatusCode.SUCCESS
        # define the command arguments with multiple usernames
        result = runner.invoke(
            app,
            [
                "status",
                "https://github.com/Allegheny-Computer-Science-202-S2025/",
                "computer-science-202-algorithm-analysis-executable-exam-3",
                "/home/gkapfham/working/teaching/github-classroom/algorithmology/github-usernames/github_usernames_spring2025.json",
                "github_access_token_fake_1234",
                "--username",
                "gkapfham",
                "--username",
                "student1",
            ],
        )
        # verify the command executed successfully
        assert result.exit_code == 0
        # verify the mocked function was called multiple times
        assert mock_get_status.call_count >= 1


def test_cli_status_command_mixed_success_failure():
    """Test the status command with mixed success and failure results."""
    # mock the functions called by the CLI
    with (
        patch("reporover.main.get_github_actions_status") as mock_get_status,
        patch(
            "reporover.main.read_usernames_from_json"
        ) as mock_read_usernames,
    ):
        # configure the mocks to simulate mixed results
        mock_read_usernames.return_value = ["gkapfham", "student1"]
        mock_get_status.side_effect = [StatusCode.SUCCESS, StatusCode.FAILURE]
        # define the command arguments with multiple usernames
        result = runner.invoke(
            app,
            [
                "status",
                "https://github.com/Allegheny-Computer-Science-202-S2025/",
                "computer-science-202-algorithm-analysis-executable-exam-3",
                "/home/gkapfham/working/teaching/github-classroom/algorithmology/github-usernames/github_usernames_spring2025.json",
                "github_access_token_fake_1234",
                "--username",
                "gkapfham",
                "--username",
                "student1",
            ],
        )
        # verify the command executed with failure exit code due to mixed results
        assert result.exit_code == 1
        # verify the mocked function was called multiple times


def test_cli_commit_command_with_all_parameters_success():
    """Test the commit command with all parameters provided for success case."""
    # mock the functions called by the CLI
    with patch("reporover.main.commit_files_to_repo") as mock_commit_files:
        # configure the mocks to simulate success
        mock_commit_files.return_value = StatusCode.SUCCESS
        # define the command arguments that match the real usage
        result = runner.invoke(
            app,
            [
                "commit",
                "https://github.com/Allegheny-Computer-Science-202-S2025/",
                "computer-science-202-algorithm-analysis-executable-exam-3",
                "/home/gkapfham/working/teaching/github-classroom/algorithmology/github-usernames/github_usernames_spring2025.json",
                "github_access_token_fake_1234",
                "/tmp/source",
                "test.py",
                "main.py",
                "Initial commit of files",
                "src",
                "--username",
                "gkapfham",
            ],
        )
        # verify the command executed successfully
        assert result.exit_code == 0
        # verify the mocked function was called
        mock_commit_files.assert_called()


def test_cli_commit_command_with_all_parameters_failure():
    """Test the commit command with all parameters provided for failure case."""
    # mock the functions called by the CLI
    with patch("reporover.main.commit_files_to_repo") as mock_commit_files:
        # configure the mocks to simulate failure
        mock_commit_files.return_value = StatusCode.FAILURE
        # define the command arguments that match the real usage
        result = runner.invoke(
            app,
            [
                "commit",
                "https://github.com/Allegheny-Computer-Science-202-S2025/",
                "computer-science-202-algorithm-analysis-executable-exam-3",
                "/home/gkapfham/working/teaching/github-classroom/algorithmology/github-usernames/github_usernames_spring2025.json",
                "github_access_token_fake_1234",
                "/tmp/source",
                "test.py",
                "main.py",
                "Initial commit of files",
                "src",
                "--username",
                "gkapfham",
            ],
        )
        # verify the command executed with failure exit code
        assert result.exit_code == 1
        # verify the mocked function was called
        mock_commit_files.assert_called()


def test_cli_commit_command_multiple_usernames_success():
    """Test the commit command with multiple usernames for success case."""
    # mock the functions called by the CLI
    with patch("reporover.main.commit_files_to_repo") as mock_commit_files:
        # configure the mocks to simulate success
        mock_commit_files.return_value = StatusCode.SUCCESS
        # define the command arguments with multiple usernames
        result = runner.invoke(
            app,
            [
                "commit",
                "https://github.com/Allegheny-Computer-Science-202-S2025/",
                "computer-science-202-algorithm-analysis-executable-exam-3",
                "/home/gkapfham/working/teaching/github-classroom/algorithmology/github-usernames/github_usernames_spring2025.json",
                "github_access_token_fake_1234",
                "/tmp/source",
                "test.py",
                "Initial commit of files",
                "src",
                "--username",
                "gkapfham",
                "--username",
                "student1",
            ],
        )
        # verify the command executed successfully
        assert result.exit_code == 0
        # verify the mocked function was called multiple times
        assert mock_commit_files.call_count >= 1


def test_cli_commit_command_mixed_success_failure():
    """Test the commit command with mixed success and failure results."""
    # mock the functions called by the CLI
    with (
        patch("reporover.main.commit_files_to_repo") as mock_commit_files,
        patch(
            "reporover.main.read_usernames_from_json"
        ) as mock_read_usernames,
    ):
        # configure the mocks to simulate mixed results
        mock_read_usernames.return_value = ["gkapfham", "student1"]
        mock_commit_files.side_effect = [
            StatusCode.SUCCESS,
            StatusCode.FAILURE,
        ]
        # define the command arguments with multiple usernames
        result = runner.invoke(
            app,
            [
                "commit",
                "https://github.com/Allegheny-Computer-Science-202-S2025/",
                "computer-science-202-algorithm-analysis-executable-exam-3",
                "/home/gkapfham/working/teaching/github-classroom/algorithmology/github-usernames/github_usernames_spring2025.json",
                "github_access_token_fake_1234",
                "/tmp/source",
                "test.py",
                "Initial commit of files",
                "src",
                "--username",
                "gkapfham",
                "--username",
                "student1",
            ],
        )
        # verify the command executed with failure exit code due to mixed results
        assert result.exit_code == 1
        # verify the mocked function was called multiple times
        assert mock_commit_files.call_count == 2


def test_cli_commit_command_multiple_files():
    """Test the commit command with multiple files for success case."""
    # mock the functions called by the CLI
    with patch("reporover.main.commit_files_to_repo") as mock_commit_files:
        # configure the mocks to simulate success
        mock_commit_files.return_value = StatusCode.SUCCESS
        # define the command arguments with multiple files
        result = runner.invoke(
            app,
            [
                "commit",
                "https://github.com/Allegheny-Computer-Science-202-S2025/",
                "computer-science-202-algorithm-analysis-executable-exam-3",
                "/home/gkapfham/working/teaching/github-classroom/algorithmology/github-usernames/github_usernames_spring2025.json",
                "github_access_token_fake_1234",
                "/tmp/source",
                "test.py",
                "main.py",
                "requirements.txt",
                "Initial commit with multiple files",
                "src",
                "--username",
                "gkapfham",
            ],
        )
        # verify the command executed successfully
        assert result.exit_code == 0
        # verify the mocked function was called
        mock_commit_files.assert_called()


def test_cli_clone_command_with_all_parameters_success():
    """Test the clone command with all parameters provided for success case."""
    # mock the functions called by the CLI
    with patch("reporover.main.clone_repo_gitpython") as mock_clone_repo:
        # configure the mocks to simulate success
        mock_clone_repo.return_value = StatusCode.SUCCESS
        # define the command arguments that match the real usage
        result = runner.invoke(
            app,
            [
                "clone",
                "https://github.com/Allegheny-Computer-Science-202-S2025/",
                "computer-science-202-algorithm-analysis-executable-exam-3",
                "/home/gkapfham/working/teaching/github-classroom/algorithmology/github-usernames/github_usernames_spring2025.json",
                "github_access_token_fake_1234",
                "/tmp/cloned-repos",
                "--username",
                "gkapfham",
            ],
        )
        # verify the command executed successfully
        assert result.exit_code == 0
        # verify the mocked function was called
        mock_clone_repo.assert_called()


def test_cli_clone_command_with_all_parameters_failure():
    """Test the clone command with all parameters provided for failure case."""
    # mock the functions called by the CLI
    with patch("reporover.main.clone_repo_gitpython") as mock_clone_repo:
        # configure the mocks to simulate failure
        mock_clone_repo.return_value = StatusCode.FAILURE
        # define the command arguments that match the real usage
        result = runner.invoke(
            app,
            [
                "clone",
                "https://github.com/Allegheny-Computer-Science-202-S2025/",
                "computer-science-202-algorithm-analysis-executable-exam-3",
                "/home/gkapfham/working/teaching/github-classroom/algorithmology/github-usernames/github_usernames_spring2025.json",
                "github_access_token_fake_1234",
                "/tmp/cloned-repos",
                "--username",
                "gkapfham",
            ],
        )
        # verify the command executed with failure exit code
        assert result.exit_code == 1
        # verify the mocked function was called
        mock_clone_repo.assert_called()


def test_cli_clone_command_multiple_usernames_success():
    """Test the clone command with multiple usernames for success case."""
    # mock the functions called by the CLI
    with patch("reporover.main.clone_repo_gitpython") as mock_clone_repo:
        # configure the mocks to simulate success
        mock_clone_repo.return_value = StatusCode.SUCCESS
        # define the command arguments with multiple usernames
        result = runner.invoke(
            app,
            [
                "clone",
                "https://github.com/Allegheny-Computer-Science-202-S2025/",
                "computer-science-202-algorithm-analysis-executable-exam-3",
                "/home/gkapfham/working/teaching/github-classroom/algorithmology/github-usernames/github_usernames_spring2025.json",
                "github_access_token_fake_1234",
                "/tmp/cloned-repos",
                "--username",
                "gkapfham",
                "--username",
                "student1",
            ],
        )
        # verify the command executed successfully
        assert result.exit_code == 0
        # verify the mocked function was called multiple times
        assert mock_clone_repo.call_count >= 1


def test_cli_clone_command_mixed_success_failure():
    """Test the clone command with mixed success and failure results."""
    # mock the functions called by the CLI
    with (
        patch("reporover.main.clone_repo_gitpython") as mock_clone_repo,
        patch(
            "reporover.main.read_usernames_from_json"
        ) as mock_read_usernames,
    ):
        # configure the mocks to simulate mixed results
        mock_read_usernames.return_value = ["gkapfham", "student1"]
        mock_clone_repo.side_effect = [StatusCode.SUCCESS, StatusCode.FAILURE]
        # define the command arguments with multiple usernames
        result = runner.invoke(
            app,
            [
                "clone",
                "https://github.com/Allegheny-Computer-Science-202-S2025/",
                "computer-science-202-algorithm-analysis-executable-exam-3",
                "/home/gkapfham/working/teaching/github-classroom/algorithmology/github-usernames/github_usernames_spring2025.json",
                "github_access_token_fake_1234",
                "/tmp/cloned-repos",
                "--username",
                "gkapfham",
                "--username",
                "student1",
            ],
        )
        # verify the command executed with failure exit code due to mixed results
        assert result.exit_code == 1
        # verify the mocked function was called multiple times
        assert mock_clone_repo.call_count == 2


def test_cli_clone_command_no_username_filter():
    """Test the clone command without username filter uses all usernames."""
    # mock the functions called by the CLI
    with (
        patch("reporover.main.clone_repo_gitpython") as mock_clone_repo,
        patch(
            "reporover.main.read_usernames_from_json"
        ) as mock_read_usernames,
    ):
        # configure the mocks to simulate success with multiple usernames
        mock_read_usernames.return_value = ["student1", "student2", "student3"]
        mock_clone_repo.return_value = StatusCode.SUCCESS
        # define the command arguments without username filter
        result = runner.invoke(
            app,
            [
                "clone",
                "https://github.com/Allegheny-Computer-Science-202-S2025/",
                "computer-science-202-algorithm-analysis-executable-exam-3",
                "/home/gkapfham/working/teaching/github-classroom/algorithmology/github-usernames/github_usernames_spring2025.json",
                "github_access_token_fake_1234",
                "/tmp/cloned-repos",
            ],
        )
        # verify the command executed successfully
        assert result.exit_code == 0
        # verify the mocked function was called for all usernames
        assert mock_clone_repo.call_count == 3


def test_cli_clone_command_username_intersection():
    """Test the clone command filters usernames correctly."""
    # mock the functions called by the CLI
    with (
        patch("reporover.main.clone_repo_gitpython") as mock_clone_repo,
        patch(
            "reporover.main.read_usernames_from_json"
        ) as mock_read_usernames,
    ):
        # configure the mocks with usernames where only some match
        mock_read_usernames.return_value = ["student1", "student2", "student3"]
        mock_clone_repo.return_value = StatusCode.SUCCESS
        # define the command arguments with specific usernames
        result = runner.invoke(
            app,
            [
                "clone",
                "https://github.com/Allegheny-Computer-Science-202-S2025/",
                "computer-science-202-algorithm-analysis-executable-exam-3",
                "/home/gkapfham/working/teaching/github-classroom/algorithmology/github-usernames/github_usernames_spring2025.json",
                "github_access_token_fake_1234",
                "/tmp/cloned-repos",
                "--username",
                "student1",
                "--username",
                "student4",
            ],
        )
        # verify the command executed successfully
        assert result.exit_code == 0
        # verify the mocked function was called only for existing username
        assert mock_clone_repo.call_count == 1
