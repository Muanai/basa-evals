import pytest
from pydantic import ValidationError

from basa_evals.core.schema import (
    GateCriteria,
    RunConfig,
    Sample,
    SampleMetadata,
    SliceConfig,
    SliceGate,
    SystemRunConfig,
)


def test_sample_negative_control_invariant():
    # Valid negative control
    s = Sample(
        id="gold-neg-0001",
        dataset_version="v1.0.0",
        slice="negative_controls_kbbi",
        raw_input="Kafka dan PostgreSQL",
        expected_output="Kafka dan PostgreSQL",
        negative_control=True,
        applied_ops=[],
    )
    assert s.negative_control is True
    assert s.applied_ops == []

    # Mismatch between raw and expected on negative control
    with pytest.raises(ValidationError, match="raw_input must be identical to expected_output"):
        Sample(
            id="gold-neg-0002",
            dataset_version="v1.0.0",
            slice="negative_controls_kbbi",
            raw_input="Kafka dan PostgreSQL",
            expected_output="kafka dan postgresql",
            negative_control=True,
            applied_ops=[],
        )

    # Negative control with non-empty applied_ops
    with pytest.raises(ValidationError, match="applied_ops must be empty"):
        Sample(
            id="gold-neg-0003",
            dataset_version="v1.0.0",
            slice="negative_controls_kbbi",
            raw_input="Kafka dan PostgreSQL",
            expected_output="Kafka dan PostgreSQL",
            negative_control=True,
            applied_ops=["lexicon_lookup"],
        )

def test_sample_applied_ops_agreement():
    # Single-phenomenon slice must have exactly 1 matching op
    s = Sample(
        id="gold-slang-0001",
        dataset_version="v1.0.0",
        slice="slang_lexical",
        raw_input="gw gamau",
        expected_output="saya tidak mau",
        negative_control=False,
        applied_ops=["lexicon_lookup"],
    )
    assert len(s.applied_ops) == 1

    # Multiple ops on single-phenomenon slice rejected
    with pytest.raises(ValidationError, match="requires exactly one"):
        Sample(
            id="gold-slang-0002",
            dataset_version="v1.0.0",
            slice="slang_lexical",
            raw_input="gw gamau",
            expected_output="saya tidak mau",
            negative_control=False,
            applied_ops=["lexicon_lookup", "repetition_collapse"],
        )

    # Mixed challenge slice requires >= 2 ops
    with pytest.raises(ValidationError, match="requires at least 2"):
        Sample(
            id="gold-mix-0001",
            dataset_version="v1.0.0",
            slice="mixed_challenge",
            raw_input="gw gamau",
            expected_output="saya tidak mau",
            negative_control=False,
            applied_ops=["lexicon_lookup"],
        )

def test_protected_entities_must_be_present():
    with pytest.raises(ValidationError, match="not present in raw_input"):
        Sample(
            id="gold-neg-0004",
            dataset_version="v1.0.0",
            slice="negative_controls_kbbi",
            raw_input="Aplikasi berjalan normal",
            expected_output="Aplikasi berjalan normal",
            negative_control=True,
            applied_ops=[],
            metadata=SampleMetadata(protected_entities=["Kafka"]),
        )

def test_gate_criteria_scale_rule():
    gate = GateCriteria(oner_max_rate=0.005, oner_zero_tolerance_below=500)
    assert gate.oner_zero_tolerance_below == 500
    assert gate.oner_max_rate == 0.005

def test_run_config_valid():
    cfg = RunConfig(
        name="pilot_210",
        dataset_version="v1.0.0",
        slices=[SliceConfig(path="challenge/neg.jsonl", slice_name="neg", exploratory=False)],
        systems=[SystemRunConfig(system_id="raw-identity", adapter="raw")],
        gate=GateCriteria(per_slice={"neg": SliceGate(oner_max_errors=0)}),
    )
    assert cfg.name == "pilot_210"
    assert len(cfg.slices) == 1
