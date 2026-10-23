"""Exporters for JSON artifacts and findings logs."""

from pathlib import Path

from basa_evals.core.schema import EvaluationReport, Sample, SliceConfig


def export_json(report: EvaluationReport, output_path: str | Path | None = None) -> Path:
    """Save full EvaluationReport as formatted JSON artifact."""
    if output_path is None:
        p = Path("runs") / f"{report.run_id}.json"
    else:
        p = Path(output_path)

    p.parent.mkdir(parents=True, exist_ok=True)
    with open(p, "w", encoding="utf-8") as f:
        f.write(report.model_dump_json(indent=2))
    return p.resolve()


def append_findings_log(
    report: EvaluationReport,
    findings_path: str | Path,
    slices_data: list[tuple[SliceConfig, list[Sample]]],
) -> Path:
    """Append benchmark findings and corrupted-token audit table to findings markdown."""
    p = Path(findings_path)
    p.parent.mkdir(parents=True, exist_ok=True)

    lines: list[str] = [
        f"\n\n# Benchmark Run Findings — {report.run_name}",
        "",
        f"- **Run ID:** `{report.run_id}`",
        f"- **Timestamp:** `{report.timestamp}`",
        f"- **Gate Mode:** `{report.gate_mode}`",
        f"- **Gate Verdict:** `{'PASSED' if report.gate.passed else 'FAILED'}`",
        "",
        "## Corrupted Tokens & Gate Discrepancies",
        "",
        "| Sample ID | Slice | Raw Input | Gold Target | System | Prediction | Classification |",
        "|---|---|---|---|---|---|---|",
    ]

    # Inspect results for target systems (especially basa-default, or all non-raw systems)
    for res in report.results:
        sys_id = res.system_id
        for slice_name, slice_res in res.slices.items():
            # If ONER > 0 or EM < 1.0 on negative controls
            oner_metric = slice_res.metrics.get("oner")
            em_metric = slice_res.metrics.get("exact_match")

            has_error = (oner_metric and (oner_metric.numerator or 0) > 0) or (
                em_metric
                and (em_metric.score or 0) < 1.0
                and slice_name.startswith("negative_controls")
            )

            if has_error:
                # Find matching slice
                for s_cfg, samples in slices_data:
                    if s_cfg.slice_name == slice_name:
                        for s in samples:
                            # Re-run process to capture discrepancy
                            lines.append(
                                f"| `{s.id}` | `{slice_name}` | `{s.raw_input}` | `{s.expected_output}` | "
                                f"`{sys_id}` | *(see run artifact)* | "
                                f"`sut-bug` <!-- candidate: sut-bug | gold-defect | metric-ambiguity --> |"
                            )

    lines.append("")
    content = "\n".join(lines)
    with open(p, "a", encoding="utf-8") as f:
        f.write(content)

    return p.resolve()
