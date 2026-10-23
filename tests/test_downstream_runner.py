"""Unit tests for DownstreamRunner and downstream benchmark reporters."""

import json
from io import StringIO
from pathlib import Path

import pytest
from rich.console import Console

from basa_evals.adapters.identity import RawAdapter
from basa_evals.adapters.simple_regex import SimpleRegexBaseline
from basa_evals.core.schema import Sample
from basa_evals.downstream.mock import MockSentimentClassifier
from basa_evals.downstream.runner import DownstreamRunner
from basa_evals.reporters.console import ConsoleReporter
from basa_evals.reporters.markdown import MarkdownReporter


@pytest.fixture
def smsa_mini_samples() -> list[Sample]:
    """Load first 15 samples from SmSA test slice."""
    repo_root = Path(__file__).parent.parent
    path = repo_root / "data/downstream/smsa_test_v1.jsonl"
    samples: list[Sample] = []
    with open(path, encoding="utf-8") as f:
        for idx, line in enumerate(f):
            if idx >= 15:
                break
            line = line.strip()
            if line:
                samples.append(Sample.model_validate(json.loads(line)))
    return samples


def test_downstream_runner_conservation_law_and_invariants(smsa_mini_samples: list[Sample]) -> None:
    """Test that DownstreamRunner satisfies conservation on raw-identity and partition invariants."""
    raw_sys = RawAdapter()
    regex_sys = SimpleRegexBaseline()
    classifier = MockSentimentClassifier()

    report = DownstreamRunner.run_benchmark(
        samples=smsa_mini_samples,
        systems=[raw_sys, regex_sys],
        classifier=classifier,
        suite_name="test-smsa",
    )

    assert report.suite_name == "test-smsa"
    assert report.task == "sentiment"
    assert report.classifier_id == "mock-sentiment"
    assert len(report.results) == 2

    raw_res = report.results[0]
    assert raw_res.system_id == "raw-identity"
    # Strict conservation law: raw-identity must have 0 deltas, 0 wins, 0 losses
    assert raw_res.delta_f1 == 0.0
    assert raw_res.delta_accuracy == 0.0
    assert raw_res.wins == 0
    assert raw_res.losses == 0
    assert raw_res.neutrals == len(smsa_mini_samples)
    assert raw_res.net_win_rate == 0.0

    # Partition invariant for all systems
    for res in report.results:
        assert res.wins + res.losses + res.neutrals == len(smsa_mini_samples)
        assert len(res.sample_results) == len(smsa_mini_samples)
        assert res.sample_count == len(smsa_mini_samples)
        assert -1.0 <= res.net_win_rate <= 1.0


def test_downstream_runner_missing_gold_label_raises() -> None:
    """Test that runner raises ValueError if any sample lacks a gold_label."""
    bad_sample = Sample(
        id="bad-01",
        dataset_version="v1.0.0",
        slice="test_slice",
        raw_input="test",
        expected_output="test",
        negative_control=True,
        gold_label=None,
    )
    raw_sys = RawAdapter()
    classifier = MockSentimentClassifier()

    with pytest.raises(ValueError, match="missing gold_label"):
        DownstreamRunner.run_benchmark(
            samples=[bad_sample],
            systems=[raw_sys],
            classifier=classifier,
        )


def test_downstream_reporters_render(smsa_mini_samples: list[Sample]) -> None:
    """Test console and markdown reporters for downstream benchmark."""
    raw_sys = RawAdapter()
    regex_sys = SimpleRegexBaseline()
    classifier = MockSentimentClassifier()

    report = DownstreamRunner.run_benchmark(
        samples=smsa_mini_samples,
        systems=[raw_sys, regex_sys],
        classifier=classifier,
        suite_name="test-smsa",
    )

    # 1. Console Reporter
    buf = StringIO()
    console = Console(file=buf, force_terminal=True, color_system="standard")
    reporter = ConsoleReporter(console=console)
    reporter.render_downstream_benchmark(report)

    output = buf.getvalue()
    assert "Tier 3: Applied Downstream Benchmark" in output or "Downstream Benchmark" in output
    assert "raw-identity" in output
    assert "simple-regex" in output
    assert "mock-sentiment" in output

    # 2. Markdown Reporter
    md_output = MarkdownReporter.render_downstream_benchmark(report)
    assert "# Downstream Task Benchmark Report" in md_output or "Downstream" in md_output
    assert "`raw-identity`" in md_output
    assert "`simple-regex`" in md_output
    assert "| System | Task | Classifier |" in md_output or "| System |" in md_output
