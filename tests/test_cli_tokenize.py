from pathlib import Path

from typer.testing import CliRunner

from basa_evals.cli import app

runner = CliRunner()


def test_cli_list_tokenizers():
    result = runner.invoke(app, ["list-tokenizers"])
    assert result.exit_code == 0
    assert "mock-subword" in result.output
    assert "gpt-4o" in result.output


def test_cli_tokenize_mock_run(tmp_path: Path):
    result = runner.invoke(
        app,
        [
            "tokenize",
            "--suite",
            "configs/suites/pilot_210.yaml",
            "--systems",
            "raw-identity",
            "--tokenizers",
            "mock-subword",
            "--output-dir",
            str(tmp_path),
        ],
    )
    assert result.exit_code == 0
    assert "Tier 2: Multi-Tokenizer Efficiency Benchmark" in result.output
    # Check that report files were written to output-dir
    json_reports = list(tmp_path.glob("*.json"))
    md_reports = list(tmp_path.glob("*.md"))
    assert len(json_reports) == 1
    assert len(md_reports) == 1
