"""Corpus-level ratio-of-sums aggregation and alignment evaluation."""

import unicodedata
from basa_evals.core.alignment import align_reference, project_hypothesis
from basa_evals.core.schema import MetricValue, Prediction, Sample
from basa_evals.core.tokenizer import tokenize
from basa_evals.metrics.linguistic import (
    exact_match_casefold,
    exact_match_exact,
    levenshtein_distance,
)
from basa_evals.metrics.preservation import check_entity_preservation


def compute_corpus_metrics(
    samples: list[Sample],
    predictions: list[Prediction],
) -> dict[str, MetricValue]:
    """Compute corpus-level ratio-of-sums metrics over aligned samples and predictions."""
    preds_by_id = {p.sample_id: p for p in predictions}
    for s in samples:
        if s.id not in preds_by_id:
            raise ValueError(f"Missing prediction for sample '{s.id}'")

    n_samples = len(samples)

    em_exact_sum = 0
    em_casefold_sum = 0

    total_char_dist = 0
    total_char_len = 0

    total_word_dist = 0
    total_word_len = 0

    total_on_errors = 0
    total_clean_tokens = 0
    total_sub_del = 0
    total_ins = 0
    total_preserved_clean = 0
    oner_excluded: list[str] = []

    total_un_errors = 0
    total_noisy_tokens = 0
    total_correctly_fixed = 0
    uner_excluded: list[str] = []

    total_entities_preserved = 0
    total_entities_expected = 0
    entity_excluded: list[str] = []

    for s in samples:
        p = preds_by_id[s.id]
        pred_text = p.predicted_text
        gold_text = s.expected_output
        raw_text = s.raw_input

        # Exact Match
        em_exact = exact_match_exact(pred_text, gold_text)
        em_casefold = exact_match_casefold(pred_text, gold_text)
        em_exact_sum += int(em_exact)
        em_casefold_sum += int(em_casefold)

        # CER
        pred_nfc = unicodedata.normalize("NFC", pred_text)
        gold_nfc = unicodedata.normalize("NFC", gold_text)
        total_char_dist += levenshtein_distance(pred_nfc, gold_nfc)
        total_char_len += max(1, len(gold_nfc))

        # WER
        pred_tokens = tokenize(pred_text)
        gold_tokens = tokenize(gold_text)
        raw_tokens = tokenize(raw_text)

        pred_tok_texts = [unicodedata.normalize("NFC", t.text) for t in pred_tokens]
        gold_tok_texts = [unicodedata.normalize("NFC", t.text) for t in gold_tokens]
        total_word_dist += levenshtein_distance(pred_tok_texts, gold_tok_texts)
        total_word_len += max(1, len(gold_tok_texts))

        # ONER & UNER via reference alignment and hypothesis projection
        ref_spans = align_reference(raw_tokens, gold_tokens)
        alignment_res = project_hypothesis(ref_spans, pred_tokens)

        total_on_errors += alignment_res.on_errors
        total_clean_tokens += alignment_res.clean_tokens
        total_sub_del += alignment_res.on_substitution_or_deletion
        total_ins += alignment_res.on_insertion
        total_preserved_clean += alignment_res.preserved_clean
        if alignment_res.clean_tokens == 0:
            oner_excluded.append(s.id)

        total_un_errors += alignment_res.un_errors
        total_noisy_tokens += alignment_res.noisy_tokens
        total_correctly_fixed += alignment_res.correctly_fixed
        if alignment_res.noisy_tokens == 0:
            uner_excluded.append(s.id)

        # Entity Preservation
        if not s.metadata.protected_entities:
            entity_excluded.append(s.id)
        else:
            pres, exp = check_entity_preservation(pred_text, s.metadata.protected_entities)
            total_entities_preserved += pres
            total_entities_expected += exp

    # Ratio-of-sums calculation
    return {
        "exact_match": MetricValue(
            score=em_exact_sum / n_samples if n_samples > 0 else None,
            numerator=float(em_exact_sum),
            denominator=float(n_samples),
            sample_count=n_samples,
            excluded_samples=[],
        ),
        "exact_match_casefold": MetricValue(
            score=em_casefold_sum / n_samples if n_samples > 0 else None,
            numerator=float(em_casefold_sum),
            denominator=float(n_samples),
            sample_count=n_samples,
            excluded_samples=[],
        ),
        "cer": MetricValue(
            score=total_char_dist / total_char_len if total_char_len > 0 else None,
            numerator=float(total_char_dist),
            denominator=float(total_char_len),
            sample_count=n_samples,
            excluded_samples=[],
        ),
        "wer": MetricValue(
            score=total_word_dist / total_word_len if total_word_len > 0 else None,
            numerator=float(total_word_dist),
            denominator=float(total_word_len),
            sample_count=n_samples,
            excluded_samples=[],
        ),
        "oner": MetricValue(
            score=total_on_errors / total_clean_tokens if total_clean_tokens > 0 else None,
            numerator=float(total_on_errors),
            denominator=float(total_clean_tokens),
            sample_count=n_samples,
            excluded_samples=oner_excluded if total_clean_tokens > 0 else [s.id for s in samples],
            details={
                "on_substitution_or_deletion": total_sub_del,
                "on_insertion": total_ins,
                "preserved_clean": total_preserved_clean,
            },
        ),
        "uner": MetricValue(
            score=total_un_errors / total_noisy_tokens if total_noisy_tokens > 0 else None,
            numerator=float(total_un_errors),
            denominator=float(total_noisy_tokens),
            sample_count=n_samples,
            excluded_samples=uner_excluded if total_noisy_tokens > 0 else [s.id for s in samples],
            details={"correctly_fixed": total_correctly_fixed},
        ),
        "entity_preservation": MetricValue(
            score=(
                total_entities_preserved / total_entities_expected
                if total_entities_expected > 0
                else None
            ),
            numerator=float(total_entities_preserved),
            denominator=float(total_entities_expected),
            sample_count=n_samples,
            excluded_samples=entity_excluded,
        ),
    }
