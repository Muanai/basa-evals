"""Downstream task evaluation execution harness."""

import platform
import uuid
from datetime import UTC, datetime

from basa_evals.adapters.base import BasePreprocessor
from basa_evals.core.provenance import get_git_commit
from basa_evals.core.schema import (
    DownstreamBenchmarkReport,
    DownstreamTaskSummary,
    RunProvenance,
    Sample,
)
from basa_evals.downstream.base import ClassifierAdapter
from basa_evals.metrics.downstream import compute_downstream_summary


class DownstreamRunner:
    """Execution runner evaluating text normalization systems against downstream classifiers."""

    @classmethod
    def run_benchmark(
        cls,
        samples: list[Sample],
        systems: list[BasePreprocessor],
        classifier: ClassifierAdapter,
        suite_name: str = "default",
        task: str | None = None,
    ) -> DownstreamBenchmarkReport:
        """Run downstream benchmark across preprocessors using the provided classifier."""
        if not samples:
            raise ValueError("Cannot run downstream benchmark with empty samples.")

        task_name = task or classifier.task
        run_id = str(uuid.uuid4())
        timestamp = datetime.now(UTC).isoformat()

        provenance = RunProvenance(
            git_commit=get_git_commit(),
            basa_evals_version="0.1.0a0",
            python_version=platform.python_version(),
            platform_system=platform.system(),
            platform_machine=platform.machine(),
        )

        sample_ids: list[str] = []
        raw_texts: list[str] = []
        gold_labels: list[str] = []

        for s in samples:
            if s.gold_label is None:
                raise ValueError(
                    f"Sample '{s.id}' is missing gold_label required for downstream task."
                )
            sample_ids.append(s.id)
            raw_texts.append(s.raw_input)
            gold_labels.append(s.gold_label)

        # 1. Compute baseline predictions on unnormalized raw text
        raw_preds = classifier.predict_batch(raw_texts)

        results: list[DownstreamTaskSummary] = []
        classes = sorted(classifier.classes)

        for system in systems:
            pred_texts = system.process_batch(raw_texts)
            norm_preds = classifier.predict_batch(pred_texts)

            summary = compute_downstream_summary(
                system_id=system.system_id,
                classifier_id=classifier.classifier_id,
                task=task_name,
                classes=classes,
                sample_ids=sample_ids,
                raw_texts=raw_texts,
                pred_texts=pred_texts,
                gold_labels=gold_labels,
                raw_preds=raw_preds,
                norm_preds=norm_preds,
            )
            results.append(summary)

        return DownstreamBenchmarkReport(
            run_id=run_id,
            timestamp=timestamp,
            provenance=provenance,
            suite_name=suite_name,
            task=task_name,
            classifier_id=classifier.classifier_id,
            systems=[sys.system_id for sys in systems],
            results=results,
        )
