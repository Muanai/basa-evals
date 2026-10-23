from basa_evals.adapters.identity import RawAdapter
from basa_evals.adapters.simple_regex import SimpleRegexBaseline
from basa_evals.core.schema import Sample
from basa_evals.tokenizers.mock import MockTokenizerAdapter
from basa_evals.tokenizers.runner import TokenizerRunner


def test_tokenizer_runner_conservation_law():
    samples = [
        Sample(
            id="s1",
            dataset_version="0.1.0",
            tier="intrinsic",
            slice="repetition_reduction",
            domain="test",
            raw_input="iyaaaa halo",
            expected_output="iya halo",
            negative_control=False,
            applied_ops=["repetition_collapse"],
        ),
        Sample(
            id="s2",
            dataset_version="0.1.0",
            tier="intrinsic",
            slice="negative_controls_kbbi",
            domain="test",
            raw_input="Aplikasi ini berjalan cepat.",
            expected_output="Aplikasi ini berjalan cepat.",
            negative_control=True,
        ),

    ]

    tok = MockTokenizerAdapter()
    raw_sys = RawAdapter()

    report = TokenizerRunner.run_benchmark(
        samples=samples,
        systems=[raw_sys],
        tokenizers=[tok],
        suite_name="test_suite",
    )

    assert report.suite_name == "test_suite"
    assert len(report.results) == 1
    res = report.results[0]
    assert res.system_id == "raw-identity"
    assert res.tokenizer_id == "mock-subword"

    # Strict conservation invariant for RawAdapter:
    assert res.total_pred_tokens == res.total_raw_tokens
    assert res.corpus_compression_ratio == 1.0
    assert res.net_savings_rate == 0.0
    assert res.mean_delta_sfi == 0.0

    for slice_summary in res.slice_breakdowns.values():
        assert slice_summary.corpus_compression_ratio == 1.0
        assert slice_summary.net_savings_rate == 0.0
        assert slice_summary.delta_sfi == 0.0
        assert slice_summary.compression_count == 0
        assert slice_summary.inflation_count == 0
        assert slice_summary.neutral_count == slice_summary.total_samples


def test_tokenizer_runner_multi_system():
    samples = [
        Sample(
            id="s1",
            dataset_version="0.1.0",
            tier="intrinsic",
            slice="repetition_reduction",
            domain="test",
            raw_input="iyaaaa halo",
            expected_output="iya halo",
            negative_control=False,
            applied_ops=["repetition_collapse"],
        )
    ]

    tok = MockTokenizerAdapter()
    raw_sys = RawAdapter()
    regex_sys = SimpleRegexBaseline()

    report = TokenizerRunner.run_benchmark(
        samples=samples,
        systems=[raw_sys, regex_sys],
        tokenizers=[tok],
        suite_name="multi_sys_suite",
    )

    assert len(report.results) == 2
    systems_in_report = [r.system_id for r in report.results]
    assert "raw-identity" in systems_in_report
    assert "simple-regex" in systems_in_report
    assert report.provenance.python_version != ""
