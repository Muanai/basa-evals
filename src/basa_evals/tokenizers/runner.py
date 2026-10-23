"""Tokenizer evaluation execution harness."""

from datetime import datetime, timezone
import platform
import uuid

from basa_evals.adapters.base import BasePreprocessor
from basa_evals.core.provenance import get_git_commit
from basa_evals.core.schema import (
    RunProvenance,
    Sample,
    SampleTokenizerResult,
    SystemTokenizerSummary,
    TokenizerBenchmarkReport,
)
from basa_evals.metrics.tokenization import (
    aggregate_tokenizer_system,
    compute_sample_token_stats,
)
from basa_evals.tokenizers.base import TokenizerAdapter


class TokenizerRunner:
    """Execution runner evaluating text normalization systems against subword tokenizers."""

    @classmethod
    def run_benchmark(
        cls,
        samples: list[Sample],
        systems: list[BasePreprocessor],
        tokenizers: list[TokenizerAdapter],
        suite_name: str = "default",
    ) -> TokenizerBenchmarkReport:
        """Run benchmark across systems and tokenizers over the provided sample slice."""
        run_id = str(uuid.uuid4())
        timestamp = datetime.now(timezone.utc).isoformat()

        provenance = RunProvenance(
            git_commit=get_git_commit(),
            basa_evals_version="0.1.0a0",
            python_version=platform.python_version(),
            platform_system=platform.system(),
            platform_machine=platform.machine(),
        )

        raw_texts = [s.raw_input for s in samples]
        results: list[SystemTokenizerSummary] = []

        for system in systems:
            pred_texts = system.process_batch(raw_texts)

            for tokenizer in tokenizers:
                sample_results: list[SampleTokenizerResult] = []

                for sample, raw, pred in zip(samples, raw_texts, pred_texts, strict=True):
                    stat = compute_sample_token_stats(
                        sample_id=sample.id,
                        slice_name=sample.slice,
                        tokenizer_id=tokenizer.tokenizer_id,
                        raw_text=raw,
                        pred_text=pred,
                        gold_text=sample.expected_output,
                        tokenizer=tokenizer,
                    )
                    sample_results.append(stat)

                sys_summary = aggregate_tokenizer_system(
                    system_id=system.system_id,
                    tokenizer_id=tokenizer.tokenizer_id,
                    results=sample_results,
                )
                results.append(sys_summary)

        return TokenizerBenchmarkReport(
            run_id=run_id,
            timestamp=timestamp,
            provenance=provenance,
            suite_name=suite_name,
            systems=[sys.system_id for sys in systems],
            tokenizers=[tok.tokenizer_id for tok in tokenizers],
            results=results,
        )
