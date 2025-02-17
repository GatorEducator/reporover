"""Test the main module of the reporepo command-line interface."""

from typer.testing import CliRunner

from reporepo.main import app

runner = CliRunner()


def test_cli_provides_help_no_error():
    """Ensure that the CLI interface is working as expected when run with --help."""
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "Usage" in result.output
