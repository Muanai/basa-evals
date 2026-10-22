"""Evaluation runner coordinating systems, dataset slices, metrics, and gates."""

from datetime import datetime, timezone
from pathlib import Path
import platform
from typing import Any
import uuid

from basa_evals.core.gate import evaluate_suite_gate
from basa_evals.core.loader import load_suite, resolve_slice
from basa_evals.core.provenance import compute_file_sha256, get_git_commit
from basa_evals.core.registry import Registry
from basa_evals.core.schema import (
    DatasetProvenance,
    EvaluationReport,
    Prediction,
    RunConfig,
    Sample,
    SliceConfig,
    SliceResult,
    SystemProvenance,
    SystemResult,
)
from basa_evals.metrics.aggregate import compute_corpus_metrics


class EvaluationRunner:
    """Execution engine for running suite benchmarks across Systems Under Test."""

    def __init__(
        self,
        run_config: RunConfig,
        slices_data: list[tuple[SliceConfig, list[Sample]]] | None = None,
        target_system: str | None = None,
    ) -> None:
        self.run_config = run_config
        self.target_system = target_system

        if slices_data is None:
            # Load slices from config paths
            self.slices_data: list[tuple[SliceConfig, list[Sample]]] = []
            for s_cfg in self.run_config.slices:
                slice_path = resolve_slice(s_cfg.path)
                import json

                samples: list[Sample] = []
                with open(slice_path, "r", encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if line:
                            samples.append(Sample.model_validate(json.loads(line)))
                self.slices_data.append((s_cfg, samples))
        else:
            self.slices_data = slices_data

    @classmethod
    def from_suite_path(
        cls,
        suite_path: str | Path,
        target_system: str | None = None,
    ) -> "EvaluationRunner":
        """Instantiate runner from suite file or suite name."""
        run_config, slices_data = load_suite(suite_path)
        return cls(run_config, slices_data, target_system=target_system)

    def run(
        self,
        no_gate: bool = False,
        target_system: str | None = None,
    ) -> EvaluationReport:
        """Execute full evaluation run and produce auditable EvaluationReport."""
        target_sys_id = target_system or self.target_system
        if target_sys_id is None:
            if len(self.run_config.systems) == 1:
                target_sys_id = self.run_config.systems[0].system_id
            elif any(s.system_id == "basa-default" for s in self.run_config.systems):
                target_sys_id = "basa-default"
            else:
                target_sys_id = self.run_config.systems[0].system_id

        # 1. Dataset provenance
        dataset_provenances: list[DatasetProvenance] = []
        for s_cfg, samples in self.slices_data:
            resolved_p = resolve_slice(s_cfg.path)
            dataset_provenances.append(
                DatasetProvenance(
                    path=s_cfg.path,
                    slice_name=s_cfg.slice_name,
                    sha256=compute_file_sha256(resolved_p),
                    rows=len(samples),
                )
            )

        # 2. System evaluation
        system_provenances: list[SystemProvenance] = []
        system_results: list[SystemResult] = []

        all_system_slice_metrics: dict[str, dict[str, Any]] = {}

        for sys_cfg in self.run_config.systems:
            adapter = Registry.get(
                sys_cfg.adapter,
                system_id=sys_cfg.system_id,
                params=sys_cfg.params,
                **sys_cfg.params,
            )
            system_provenances.append(
                SystemProvenance(
                    system_id=sys_cfg.system_id,
                    adapter=sys_cfg.adapter,
                    version=adapter.version,
                    params=sys_cfg.params,
                )
            )

            slice_results: dict[str, SliceResult] = {}
            sys_slice_metrics: dict[str, Any] = {}
            all_samples_corpus: list[Sample] = []
            all_preds_corpus: list[Prediction] = []

            for s_cfg, samples in self.slices_data:
                raw_texts = [s.raw_input for s in samples]
                output_texts = adapter.process_batch(raw_texts)
                if len(output_texts) != len(raw_texts):
                    raise RuntimeError(
                        f"System '{sys_cfg.system_id}' returned {len(output_texts)} items "
                        f"for batch of {len(raw_texts)}."
                    )

                predictions = [
                    Prediction(
                        sample_id=s.id,
                        system_id=sys_cfg.system_id,
                        predicted_text=pred,
                    )
                    for s, pred in zip(samples, output_texts)
                ]

                metrics = compute_corpus_metrics(samples, predictions)
                slice_results[s_cfg.slice_name] = SliceResult(
                    slice_name=s_cfg.slice_name,
                    exploratory=s_cfg.exploratory,
                    sample_count=len(samples),
                    metrics=metrics,
                )
                sys_slice_metrics[s_cfg.slice_name] = metrics

                all_samples_corpus.extend(samples)
                all_preds_corpus.extend(predictions)

            aggregate_metrics = compute_corpus_metrics(all_samples_corpus, all_preds_corpus)
            system_results.append(
                SystemResult(
                    system_id=sys_cfg.system_id,
                    system_version=adapter.version,
                    aggregate=aggregate_metrics,
                    slices=slice_results,
                )
            )
            all_system_slice_metrics[sys_cfg.system_id] = sys_slice_metrics

        # 3. Gate evaluation on target system
        target_metrics = all_system_slice_metrics.get(target_sys_id, {})
        gate_result = evaluate_suite_gate(
            self.run_config.gate,
            self.run_config.slices,
            target_metrics,
        )

        gate_mode = "enforced"
        if no_gate:
            gate_mode = "advisory"
            gate_result.passed = True

        return EvaluationReport(
            run_id=str(uuid.uuid4()),
            timestamp=datetime.now(timezone.utc).isoformat(),
            run_name=self.run_config.name,
            evals_version="0.1.0a0",
            python_version=platform.python_version(),
            git_commit=get_git_commit(),
            dataset_version=self.run_config.dataset_version,
            gate_mode=gate_mode,
            datasets=dataset_provenances,
            systems=system_provenances,
            results=system_results,
            gate=gate_result,
        )
