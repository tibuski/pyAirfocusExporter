import pytest
from click.testing import CliRunner
from pyairfocusexporter.cli import cli


def test_cli_help() -> None:
    runner = CliRunner()
    result = runner.invoke(cli, ["--help"])
    assert result.exit_code == 0
    assert "Export airfocus workspaces" in result.output


def test_cli_no_args() -> None:
    runner = CliRunner()
    result = runner.invoke(cli)
    assert result.exit_code == 0
    assert "Usage:" in result.output


def test_cli_export_help() -> None:
    runner = CliRunner()
    result = runner.invoke(cli, ["export", "--help"])
    assert result.exit_code == 0
    assert "--workspace-id" in result.output
    assert "--target" in result.output
    assert "--dry-run" in result.output
    assert "--ignore-ssl" in result.output
