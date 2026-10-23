"""CLI integration tests for downstream classification benchmark commands."""

import json
from pathlib import Path

from typer.testing import CliRunner

from basa_evals.cli import app

runner = CliRunner()


def test_cli_list_classifiers() -> None:
    result = runner.invoke(app, ["list-classifiers"])
    assert result.exit_code == 0
    assert "mock-sentiment" in result.output
    assert "hf-smsa" in result.output
    assert "sentiment" in result.output


def test_cli_downstream_mock_run(tmp_path: Path) -> None:
    result = runner.invoke(
        app,
        [
            "downstream",
            "--suite",
            "configs/suites/downstream_smsa.yaml",
            "--systems",
            "raw-identity,simple-regex",
            "--classifier",
            "mock-sentiment",
            "--output-dir",
            str(tmp_path),
        ],
    )
    assert result.exit_code == 0
    assert "Tier 3: Applied Downstream Benchmark" in result.output
    assert "raw-identity" in result.output
    assert "simple-regex" in result.output

    # Check that report files were written to output-dir
    json_reports = list(tmp_path.glob("*.json"))
    md_reports = list(tmp_path.glob("*.md"))
    assert len(json_reports) == 1
    assert len(md_reports) == 1

    with open(json_reports[0], encoding="utf-8") as f:
        data = json.load(f)
    assert data["task"] == "sentiment"
    assert data["classifier_id"] == "mock-sentiment"
    assert data["systems"] == ["raw-identity", "simple-regex"]
    assert len(data["results"]) == 2
