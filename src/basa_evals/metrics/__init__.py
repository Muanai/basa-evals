"""Metrics engine for linguistic error rates, preservation, and aggregation."""

from basa_evals.metrics.linguistic import (
    character_error_rate,
    exact_match_casefold,
    exact_match_exact,
    word_error_rate,
)
from basa_evals.metrics.preservation import check_entity_preservation
from basa_evals.metrics.aggregate import compute_corpus_metrics

__all__ = [
    "exact_match_exact",
    "exact_match_casefold",
    "character_error_rate",
    "word_error_rate",
    "check_entity_preservation",
    "compute_corpus_metrics",
]
