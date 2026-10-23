"""Tests for scale-aware gatekeeper logic and threshold rules."""

from basa_evals.core.gate import evaluate_slice_gate
from basa_evals.core.schema import GateCriteria, MetricValue, SliceGate


def test_gate_integer_zero_tolerance_under_500() -> None:
    gate = GateCriteria(
        oner_max_rate=0.005,
        oner_zero_tolerance_below=500,
        per_slice={"neg_slice": SliceGate(entity_preservation_min=1.0)},
    )
    # 1 error on 150 clean tokens must fail under zero-tolerance
    metrics = {
        "oner": MetricValue(score=0.0067, numerator=1.0, denominator=150.0, sample_count=30),
        "entity_preservation": MetricValue(
            score=1.0, numerator=30.0, denominator=30.0, sample_count=30
        ),
    }
    checks = evaluate_slice_gate(gate, "neg_slice", exploratory=False, metrics=metrics)
    oner_check = next(c for c in checks if c.criterion == "oner")
    assert oner_check.passed is False
    assert oner_check.observed == 1.0
    assert oner_check.threshold == 0.0


def test_exploratory_slice_excluded() -> None:
    gate = GateCriteria()
    checks = evaluate_slice_gate(gate, "mixed_challenge", exploratory=True, metrics={})
    assert len(checks) == 0


def test_gate_scale_rule_above_500() -> None:
    gate = GateCriteria(
        oner_max_rate=0.005,
        oner_zero_tolerance_below=500,
        per_slice={"scaled_slice": SliceGate(uner_max_rate=0.15)},
    )
    # 1000 clean tokens: allowed = ceil(0.005 * 1000) - 1 = 5 - 1 = 4 errors allowed
    # 4 errors on 1000 clean tokens: passes
    metrics_pass = {
        "oner": MetricValue(score=0.004, numerator=4.0, denominator=1000.0, sample_count=100),
        "uner": MetricValue(score=0.10, numerator=10.0, denominator=100.0, sample_count=100),
    }
    checks = evaluate_slice_gate(gate, "scaled_slice", exploratory=False, metrics=metrics_pass)
    oner_check = next(c for c in checks if c.criterion == "oner")
    assert oner_check.passed is True
    assert oner_check.threshold == 4.0

    # 5 errors on 1000 clean tokens: fails
    metrics_fail = {
        "oner": MetricValue(score=0.005, numerator=5.0, denominator=1000.0, sample_count=100),
        "uner": MetricValue(score=0.10, numerator=10.0, denominator=100.0, sample_count=100),
    }
    checks_fail = evaluate_slice_gate(gate, "scaled_slice", exploratory=False, metrics=metrics_fail)
    oner_fail = next(c for c in checks_fail if c.criterion == "oner")
    assert oner_fail.passed is False
