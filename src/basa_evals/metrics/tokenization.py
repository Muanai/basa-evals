from __future__ import annotations

from collections import defaultdict
from typing import TYPE_CHECKING

from basa_evals.core.schema import (
    SampleTokenizerResult,
    SliceTokenizerSummary,
    SystemTokenizerSummary,
)

if TYPE_CHECKING:
    from basa_evals.tokenizers.base import TokenizerAdapter


def compute_sfi(text: str, token_count: int) -> float:
    """Compute Subword Fragmentation Index (SFI) = tokens / whitespace words.

    If text is empty or contains only whitespace, returns 0.0 safely.
    """
    words = len(text.strip().split())
    if words == 0:
        return 0.0
    return token_count / words


def compute_sample_token_stats(
    sample_id: str,
    slice_name: str,
    tokenizer_id: str,
    raw_text: str,
    pred_text: str,
    gold_text: str,
    tokenizer: TokenizerAdapter,
) -> SampleTokenizerResult:
    """Compute subword token counts and SFI metrics for a single sample."""
    raw_tokens = tokenizer.count_tokens(raw_text)
    pred_tokens = tokenizer.count_tokens(pred_text)
    gold_tokens = tokenizer.count_tokens(gold_text)

    raw_sfi = compute_sfi(raw_text, raw_tokens)
    pred_sfi = compute_sfi(pred_text, pred_tokens)

    compression_ratio = raw_tokens / max(1, pred_tokens)
    token_delta = raw_tokens - pred_tokens

    return SampleTokenizerResult(
        sample_id=sample_id,
        slice_name=slice_name,
        tokenizer_id=tokenizer_id,
        raw_tokens=raw_tokens,
        pred_tokens=pred_tokens,
        gold_tokens=gold_tokens,
        raw_sfi=raw_sfi,
        pred_sfi=pred_sfi,
        compression_ratio=compression_ratio,
        token_delta=token_delta,
    )


def aggregate_tokenizer_slice(
    slice_name: str,
    tokenizer_id: str,
    results: list[SampleTokenizerResult],
) -> SliceTokenizerSummary:
    """Aggregate tokenization metrics for a specific slice."""
    n = len(results)
    if n == 0:
        return SliceTokenizerSummary(
            slice_name=slice_name,
            tokenizer_id=tokenizer_id,
            total_samples=0,
            total_raw_tokens=0,
            total_pred_tokens=0,
            total_gold_tokens=0,
            corpus_compression_ratio=1.0,
            net_savings_rate=0.0,
            mean_raw_sfi=0.0,
            mean_pred_sfi=0.0,
            delta_sfi=0.0,
            compression_count=0,
            inflation_count=0,
            neutral_count=0,
        )

    total_raw = sum(r.raw_tokens for r in results)
    total_pred = sum(r.pred_tokens for r in results)
    total_gold = sum(r.gold_tokens for r in results)

    corpus_compression_ratio = total_raw / max(1, total_pred)
    net_savings_rate = (total_raw - total_pred) / max(1, total_raw)

    mean_raw_sfi = sum(r.raw_sfi for r in results) / n
    mean_pred_sfi = sum(r.pred_sfi for r in results) / n
    delta_sfi = mean_raw_sfi - mean_pred_sfi

    compression_count = sum(1 for r in results if r.token_delta > 0)
    inflation_count = sum(1 for r in results if r.token_delta < 0)
    neutral_count = sum(1 for r in results if r.token_delta == 0)

    return SliceTokenizerSummary(
        slice_name=slice_name,
        tokenizer_id=tokenizer_id,
        total_samples=n,
        total_raw_tokens=total_raw,
        total_pred_tokens=total_pred,
        total_gold_tokens=total_gold,
        corpus_compression_ratio=corpus_compression_ratio,
        net_savings_rate=net_savings_rate,
        mean_raw_sfi=mean_raw_sfi,
        mean_pred_sfi=mean_pred_sfi,
        delta_sfi=delta_sfi,
        compression_count=compression_count,
        inflation_count=inflation_count,
        neutral_count=neutral_count,
    )


def aggregate_tokenizer_system(
    system_id: str,
    tokenizer_id: str,
    results: list[SampleTokenizerResult],
) -> SystemTokenizerSummary:
    """Aggregate tokenization metrics across all slices for a preprocessor system."""
    n = len(results)
    if n == 0:
        return SystemTokenizerSummary(
            system_id=system_id,
            tokenizer_id=tokenizer_id,
            total_raw_tokens=0,
            total_pred_tokens=0,
            corpus_compression_ratio=1.0,
            net_savings_rate=0.0,
            macro_compression_ratio=1.0,
            mean_raw_sfi=0.0,
            mean_pred_sfi=0.0,
            mean_delta_sfi=0.0,
            slice_breakdowns={},
        )

    by_slice: dict[str, list[SampleTokenizerResult]] = defaultdict(list)
    for r in results:
        by_slice[r.slice_name].append(r)

    slice_breakdowns = {
        s_name: aggregate_tokenizer_slice(s_name, tokenizer_id, s_results)
        for s_name, s_results in by_slice.items()
    }

    total_raw = sum(r.raw_tokens for r in results)
    total_pred = sum(r.pred_tokens for r in results)

    corpus_compression_ratio = total_raw / max(1, total_pred)
    net_savings_rate = (total_raw - total_pred) / max(1, total_raw)
    macro_compression_ratio = sum(r.compression_ratio for r in results) / n

    mean_raw_sfi = sum(r.raw_sfi for r in results) / n
    mean_pred_sfi = sum(r.pred_sfi for r in results) / n
    mean_delta_sfi = mean_raw_sfi - mean_pred_sfi

    return SystemTokenizerSummary(
        system_id=system_id,
        tokenizer_id=tokenizer_id,
        total_raw_tokens=total_raw,
        total_pred_tokens=total_pred,
        corpus_compression_ratio=corpus_compression_ratio,
        net_savings_rate=net_savings_rate,
        macro_compression_ratio=macro_compression_ratio,
        mean_raw_sfi=mean_raw_sfi,
        mean_pred_sfi=mean_pred_sfi,
        mean_delta_sfi=mean_delta_sfi,
        slice_breakdowns=slice_breakdowns,
    )
