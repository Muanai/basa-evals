"""Tests for evaluation runner and end-to-end execution."""

from pathlib import Path

from basa_evals.core.loader import load_suite
from basa_evals.core.runner import EvaluationRunner


def test_runner_executes_suite_mock() -> None:
    repo_root = Path(__file__).parent.parent
    suite_cfg, _ = load_suite(repo_root / "configs/suites/pilot_210.yaml")
    # Restrict to raw-identity for fast unit test
    suite_cfg.systems = [s for s in suite_cfg.systems if s.system_id == "raw-identity"]
    runner = EvaluationRunner(suite_cfg)
    report = runner.run()

    assert report.run_name == "pilot_210"
    assert len(report.results) == 1
    assert report.results[0].system_id == "raw-identity"
    assert len(report.datasets) == 7
    assert len(report.systems) == 1
    assert report.gate is not None
    assert isinstance(report.gate.passed, bool)
