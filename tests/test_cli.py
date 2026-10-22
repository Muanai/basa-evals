"""Tests for Typer CLI commands, subcommands, and exit codes."""

from typer.testing import CliRunner
from basa_evals.cli import app

runner = CliRunner()


def test_cli_list_suites():
    res = runner.invoke(app, ["list-suites"])
    assert res.exit_code == 0
    assert "pilot_210" in res.stdout


def test_cli_list_systems():
    res = runner.invoke(app, ["list-systems"])
    assert res.exit_code == 0
    assert "raw" in res.stdout
    assert "simple_regex" in res.stdout


def test_cli_validate_dataset():
    res = runner.invoke(app, ["validate-dataset"])
    assert res.exit_code == 0
    assert "valid" in res.stdout.lower()


def test_cli_run_no_gate():
    res = runner.invoke(app, ["run", "--suite", "pilot_210", "--system", "raw-identity", "--no-gate"])
    assert res.exit_code == 0
    assert "raw-identity" in res.stdout
