from basa_evals.adapters.identity import RawAdapter
from basa_evals.core.schema import Sample
from basa_evals.reporters.console import ConsoleReporter
from basa_evals.reporters.markdown import MarkdownReporter
from basa_evals.tokenizers.mock import MockTokenizerAdapter
from basa_evals.tokenizers.runner import TokenizerRunner


def test_tokenizer_reporters_render() -> None:
    samples = [
        Sample(
            id="s1",
            dataset_version="0.1.0",
            slice="repetition_reduction",

            domain="test",
            raw_input="iyaaaa halo",
            expected_output="iya halo",
            negative_control=False,
            applied_ops=["repetition_collapse"],
        )
    ]
    raw_sys = RawAdapter()
    tok = MockTokenizerAdapter()

    report = TokenizerRunner.run_benchmark(
        samples=samples,
        systems=[raw_sys],
        tokenizers=[tok],
        suite_name="test_pilot",
    )

    # 1. Test Markdown generation
    md = MarkdownReporter.render_tokenizer_benchmark(report)
    assert "# Multi-Tokenizer Efficiency Benchmark Report" in md
    assert "mock-subword" in md
    assert "raw-identity" in md
    assert "Savings (%)" in md
    assert "repetition_reduction" in md

    # 2. Test Console formatting (must not raise)
    console_reporter = ConsoleReporter()
    console_reporter.render_tokenizer_benchmark(report)
