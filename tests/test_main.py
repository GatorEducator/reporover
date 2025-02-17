"""Test the main module of the reporepo command-line interface."""

import pytest
from rich.console import Console
from rich.progress import Progress
from typer.testing import CliRunner

from reporepo.main import app, print_json_string

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


def test_print_json_string_empty(progress, capsys):
    """Confirm that the print_json_string function works correctly with an empty JSON string."""
    json_string = "{}"
    print_json_string(json_string, progress)
    captured = capsys.readouterr()
    assert captured.out == ""


def test_print_json_string_single_key_value(progress, capsys):
    """Confirm that the print_json_string function works correctly with a single key-value pair."""
    json_string = '{"key": "value"}'
    print_json_string(json_string, progress)
    captured = capsys.readouterr()
    assert "key: value" in captured.out


def test_print_json_string_multiple_key_values(progress, capsys):
    """Confirm that the print_json_string function works correctly with multiple key-value pairs."""
    json_string = '{"key1": "value1", "key2": "value2"}'
    print_json_string(json_string, progress)
    captured = capsys.readouterr()
    assert "key1: value1" in captured.out


def test_print_json_string_special_characters(progress, capsys):
    """Confirm that the print_json_string function works correctly with special characters in the JSON string."""
    json_string = '{"key!@#": "value$%^"}'
    print_json_string(json_string, progress)
    captured = capsys.readouterr()
    assert "key!@#: value$%^" in captured.out
