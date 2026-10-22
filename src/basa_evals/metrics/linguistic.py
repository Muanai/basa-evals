"""Linguistic metrics: Exact Match, Character Error Rate, and Word Error Rate."""

from typing import Any, Sequence
import unicodedata
from basa_evals.core.tokenizer import tokenize


def levenshtein_distance(seq1: Sequence[Any], seq2: Sequence[Any]) -> int:
    """Compute standard Levenshtein edit distance with unit weights."""
    n, m = len(seq1), len(seq2)
    if n == 0:
        return m
    if m == 0:
        return n

    prev_row = list(range(m + 1))
    curr_row = [0] * (m + 1)

    for i in range(1, n + 1):
        curr_row[0] = i
        item1 = seq1[i - 1]
        for j in range(1, m + 1):
            cost = 0 if item1 == seq2[j - 1] else 1
            curr_row[j] = min(
                prev_row[j] + 1,      # deletion
                curr_row[j - 1] + 1,  # insertion
                prev_row[j - 1] + cost,  # substitution
            )
        prev_row, curr_row = curr_row, prev_row

    return prev_row[m]


def exact_match_exact(pred: str, gold: str) -> float:
    """Exact string match after NFC normalization and whitespace stripping."""
    pred_norm = unicodedata.normalize("NFC", pred).strip()
    gold_norm = unicodedata.normalize("NFC", gold).strip()
    return 1.0 if pred_norm == gold_norm else 0.0


def exact_match_casefold(pred: str, gold: str) -> float:
    """Case-insensitive exact match after NFC normalization and whitespace stripping."""
    pred_norm = unicodedata.normalize("NFC", pred).strip().casefold()
    gold_norm = unicodedata.normalize("NFC", gold).strip().casefold()
    return 1.0 if pred_norm == gold_norm else 0.0


def character_error_rate(pred: str, gold: str) -> float:
    """Character Error Rate over NFC-normalized text."""
    pred_nfc = unicodedata.normalize("NFC", pred)
    gold_nfc = unicodedata.normalize("NFC", gold)
    denom = max(1, len(gold_nfc))
    dist = levenshtein_distance(pred_nfc, gold_nfc)
    return dist / denom


def word_error_rate(pred: str, gold: str) -> float:
    """Word Error Rate using the unified tokenizer and NFC normalization."""
    pred_tokens = [unicodedata.normalize("NFC", t.text) for t in tokenize(pred)]
    gold_tokens = [unicodedata.normalize("NFC", t.text) for t in tokenize(gold)]
    denom = max(1, len(gold_tokens))
    dist = levenshtein_distance(pred_tokens, gold_tokens)
    return dist / denom
