"""Tests for linguistic metrics, entity preservation, and corpus-level aggregation."""

from basa_evals.core.schema import Prediction, Sample, SampleMetadata
from basa_evals.metrics.aggregate import compute_corpus_metrics
from basa_evals.metrics.linguistic import (
    character_error_rate,
    exact_match_casefold,
    exact_match_exact,
    word_error_rate,
)
from basa_evals.metrics.preservation import check_entity_preservation


def test_dual_em_metrics():
    assert exact_match_exact("Kafka", "Kafka") == 1.0
    assert exact_match_exact("Kafka", "kafka") == 0.0
    assert exact_match_casefold("Kafka", "kafka") == 1.0
    assert exact_match_exact("  halo  ", "halo") == 1.0
    assert exact_match_casefold("  Halo  ", "halo") == 1.0


def test_cer_wer():
    assert character_error_rate("halo", "halo") == 0.0
    assert word_error_rate("halo dunia", "halo dunia") == 0.0
    assert character_error_rate("hlo", "halo") == 0.25
    assert word_error_rate("halo semuanya dunia", "halo dunia") == 0.5


def test_entity_preservation_subsequence():
    entities = ["Kafka", "https://gojek.com/karir"]
    # Preserved within surrounding text
    pred_ok = "kami deploy ke kafka di https://gojek.com/karir sekarang"
    preserved, expected = check_entity_preservation(pred_ok, entities)
    assert preserved == 2
    assert expected == 2

    # Shredded URL fails containment
    pred_bad = "kami deploy ke kafka di https gojek com karir sekarang"
    preserved, expected = check_entity_preservation(pred_bad, entities)
    assert preserved == 1  # only Kafka preserved
    assert expected == 2


def test_compute_corpus_metrics():
    samples = [
        Sample(
            id="s1",
            dataset_version="0.1.0",
            slice="slang_lexical",
            raw_input="gw bgt",
            expected_output="saya sangat",
            negative_control=False,
            applied_ops=["lexicon_lookup"],
            metadata=SampleMetadata(protected_entities=[]),
        ),
        Sample(
            id="s2",
            dataset_version="0.1.0",
            slice="negative_controls_kbbi",
            raw_input="Aplikasi Kafka berjalan.",
            expected_output="Aplikasi Kafka berjalan.",
            negative_control=True,
            applied_ops=[],
            metadata=SampleMetadata(protected_entities=["Kafka"]),
        ),
    ]

    predictions = [
        Prediction(sample_id="s1", system_id="sys1", predicted_text="saya sangat"),
        Prediction(sample_id="s2", system_id="sys1", predicted_text="aplikasi kafka berjalan."),
    ]

    metrics = compute_corpus_metrics(samples, predictions)

    # Check metric keys
    assert "exact_match" in metrics
    assert "exact_match_casefold" in metrics
    assert "cer" in metrics
    assert "wer" in metrics
    assert "oner" in metrics
    assert "uner" in metrics
    assert "entity_preservation" in metrics

    # s1 EM is 1.0, s2 EM is 0.0 (case difference: Aplikasi vs aplikasi)
    assert metrics["exact_match"].numerator == 1
    assert metrics["exact_match"].denominator == 2
    assert metrics["exact_match"].score == 0.5

    # Casefold EM: both match
    assert metrics["exact_match_casefold"].numerator == 2
    assert metrics["exact_match_casefold"].denominator == 2
    assert metrics["exact_match_casefold"].score == 1.0

    # Entity preservation: s1 has no entities (excluded), s2 has 1 preserved entity
    assert metrics["entity_preservation"].numerator == 1
    assert metrics["entity_preservation"].denominator == 1
    assert metrics["entity_preservation"].score == 1.0
    assert "s1" in metrics["entity_preservation"].excluded_samples

    # ONER: s1 has 0 clean tokens, s2 has 3 clean tokens (Aplikasi, Kafka, berjalan; punctuation ineligible)
    # Predicted is "aplikasi kafka berjalan." which casefolds to match gold, so 0 ON errors.
    assert metrics["oner"].numerator == 0
    assert metrics["oner"].denominator == 3
    assert metrics["oner"].score == 0.0

    # UNER: s1 has 2 noisy tokens, pred matches gold so 0 un_errors
    assert metrics["uner"].numerator == 0
    assert metrics["uner"].denominator == 2
    assert metrics["uner"].score == 0.0
