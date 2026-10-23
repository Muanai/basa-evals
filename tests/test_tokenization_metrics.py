from basa_evals.core.schema import SampleTokenizerResult
from basa_evals.metrics.tokenization import (
    aggregate_tokenizer_slice,
    aggregate_tokenizer_system,
    compute_sample_token_stats,
    compute_sfi,
)


class DummyTokenizer:
    tokenizer_id = "dummy"
    family = "bpe"
    vocab_size = 100

    def tokenize(self, text: str) -> list[str]:
        return text.split() if text.strip() else []

    def count_tokens(self, text: str) -> int:
        return len(self.tokenize(text))


def test_sfi_computation():
    # 4 subword tokens across 2 words = 2.0 SFI
    assert compute_sfi("halo dunia", 4) == 2.0
    # Single word with 3 subwords = 3.0 SFI
    assert compute_sfi("bngtttt", 3) == 3.0
    # Empty string should return 0.0 without ZeroDivisionError
    assert compute_sfi("", 0) == 0.0
    assert compute_sfi("   ", 0) == 0.0


def test_sample_token_stats():
    tok = DummyTokenizer()
    stats = compute_sample_token_stats(
        sample_id="s1",
        slice_name="repetition_reduction",
        tokenizer_id="dummy",
        raw_text="halo halo",
        pred_text="halo",
        gold_text="halo",
        tokenizer=tok,
    )
    assert stats.raw_tokens == 2
    assert stats.pred_tokens == 1
    assert stats.gold_tokens == 1
    assert stats.compression_ratio == 2.0
    assert stats.token_delta == 1
    assert stats.raw_sfi == 1.0
    assert stats.pred_sfi == 1.0


def test_aggregate_tokenizer_slice():
    # Sample 1: compression winner (raw=4, pred=2 -> delta=2)
    s1 = SampleTokenizerResult(
        sample_id="s1",
        slice_name="slice_a",
        tokenizer_id="dummy",
        raw_tokens=4,
        pred_tokens=2,
        gold_tokens=2,
        raw_sfi=2.0,
        pred_sfi=1.0,
        compression_ratio=2.0,
        token_delta=2,
    )
    # Sample 2: inflation loser (raw=2, pred=5 -> delta=-3)
    s2 = SampleTokenizerResult(
        sample_id="s2",
        slice_name="slice_a",
        tokenizer_id="dummy",
        raw_tokens=2,
        pred_tokens=5,
        gold_tokens=5,
        raw_sfi=1.0,
        pred_sfi=2.5,
        compression_ratio=0.4,
        token_delta=-3,
    )
    # Sample 3: neutral (raw=3, pred=3 -> delta=0)
    s3 = SampleTokenizerResult(
        sample_id="s3",
        slice_name="slice_a",
        tokenizer_id="dummy",
        raw_tokens=3,
        pred_tokens=3,
        gold_tokens=3,
        raw_sfi=1.0,
        pred_sfi=1.0,
        compression_ratio=1.0,
        token_delta=0,
    )

    summary = aggregate_tokenizer_slice("slice_a", "dummy", [s1, s2, s3])

    assert summary.total_samples == 3
    assert summary.total_raw_tokens == 9
    assert summary.total_pred_tokens == 10
    # Corpus compression ratio: 9 / 10 = 0.9
    assert round(summary.corpus_compression_ratio, 4) == 0.9
    # Net savings rate: (9 - 10) / 9 = -1/9 = -0.1111 (-11.11%)
    assert round(summary.net_savings_rate, 4) == round(-1 / 9, 4)
    # Partition invariant: compression + inflation + neutral == total_samples
    assert summary.compression_count == 1
    assert summary.inflation_count == 1
    assert summary.neutral_count == 1
    assert summary.compression_count + summary.inflation_count + summary.neutral_count == 3
    # SFI deltas: raw mean = (2.0 + 1.0 + 1.0)/3 = 4/3; pred mean = (1.0 + 2.5 + 1.0)/3 = 4.5/3 = 1.5
    assert round(summary.delta_sfi, 4) == round((4 / 3) - 1.5, 4)


def test_aggregate_tokenizer_system():
    s1 = SampleTokenizerResult(
        sample_id="s1",
        slice_name="slice_a",
        tokenizer_id="dummy",
        raw_tokens=10,
        pred_tokens=5,
        gold_tokens=5,
        raw_sfi=2.0,
        pred_sfi=1.0,
        compression_ratio=2.0,
        token_delta=5,
    )
    s2 = SampleTokenizerResult(
        sample_id="s2",
        slice_name="slice_b",
        tokenizer_id="dummy",
        raw_tokens=10,
        pred_tokens=10,
        gold_tokens=10,
        raw_sfi=1.0,
        pred_sfi=1.0,
        compression_ratio=1.0,
        token_delta=0,
    )

    system_summary = aggregate_tokenizer_system("basa-default", "dummy", [s1, s2])
    assert system_summary.total_raw_tokens == 20
    assert system_summary.total_pred_tokens == 15
    # Corpus compression ratio: 20 / 15 = 1.3333
    assert round(system_summary.corpus_compression_ratio, 4) == 1.3333
    assert round(system_summary.net_savings_rate, 4) == 0.25
    assert "slice_a" in system_summary.slice_breakdowns
    assert "slice_b" in system_summary.slice_breakdowns
