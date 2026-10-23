from basa_evals.core.schema import (
    RunProvenance,
    SampleTokenizerResult,
    SliceTokenizerSummary,
    SystemTokenizerSummary,
    TokenizerBenchmarkReport,
)
from basa_evals.tokenizers.base import TokenizerAdapter
from basa_evals.tokenizers.registry import TokenizerRegistry


def test_tokenizer_protocol_and_models():
    sample_res = SampleTokenizerResult(
        sample_id="test-1",
        slice_name="repetition_reduction",
        tokenizer_id="mock-tok",
        raw_tokens=10,
        pred_tokens=6,
        gold_tokens=6,
        raw_sfi=2.0,
        pred_sfi=1.2,
        compression_ratio=1.6667,
        token_delta=4,
    )
    assert sample_res.compression_ratio > 1.0
    assert sample_res.token_delta == 4

    slice_summary = SliceTokenizerSummary(
        slice_name="repetition_reduction",
        tokenizer_id="mock-tok",
        total_samples=1,
        total_raw_tokens=10,
        total_pred_tokens=6,
        total_gold_tokens=6,
        corpus_compression_ratio=1.6667,
        net_savings_rate=0.4,
        mean_raw_sfi=2.0,
        mean_pred_sfi=1.2,
        delta_sfi=0.8,
        compression_count=1,
        inflation_count=0,
        neutral_count=0,
    )
    assert slice_summary.compression_count == 1
    assert slice_summary.inflation_count == 0

    system_summary = SystemTokenizerSummary(
        system_id="basa-default",
        tokenizer_id="mock-tok",
        total_raw_tokens=10,
        total_pred_tokens=6,
        corpus_compression_ratio=1.6667,
        net_savings_rate=0.4,
        macro_compression_ratio=1.6667,
        mean_raw_sfi=2.0,
        mean_pred_sfi=1.2,
        mean_delta_sfi=0.8,
        slice_breakdowns={"repetition_reduction": slice_summary},
    )
    assert system_summary.total_pred_tokens == 6

    report = TokenizerBenchmarkReport(
        run_id="run-123",
        timestamp="2026-10-23T12:00:00Z",
        provenance=RunProvenance(
            git_commit="abc1234",
            basa_evals_version="0.1.0a0",
            python_version="3.12.6",
            platform_system="Windows",
            platform_machine="AMD64",
        ),
        suite_name="test_suite",
        systems=["basa-default"],
        tokenizers=["mock-tok"],
        results=[system_summary],
    )
    assert report.suite_name == "test_suite"


def test_tokenizer_registry():
    class DummyTokenizer:
        tokenizer_id = "test-dummy"
        family = "bpe"
        vocab_size = 50000

        def tokenize(self, text: str) -> list[str]:
            return text.split()

        def count_tokens(self, text: str) -> int:
            return len(self.tokenize(text))

    tok = DummyTokenizer()
    assert isinstance(tok, TokenizerAdapter)

    registry = TokenizerRegistry()
    registry.register(tok)
    resolved = registry.get("test-dummy")
    assert resolved.tokenizer_id == "test-dummy"
    assert "test-dummy" in registry.list_available()
