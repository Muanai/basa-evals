"""Markdown report generator with full provenance footers."""

from basa_evals.core.schema import EvaluationReport


def format_val(val: float | None, as_pct: bool = True) -> str:
    if val is None:
        return "N/A"
    return f"{val * 100:.1f}%" if as_pct else f"{val:.4f}"


def generate_markdown_report(report: EvaluationReport) -> str:
    """Generate Markdown representation of an EvaluationReport."""
    lines: list[str] = [
        f"# Evaluation Run: {report.run_name}",
        "",
        f"- **Run ID:** `{report.run_id}`",
        f"- **Timestamp:** `{report.timestamp}`",
        f"- **Dataset Version:** `{report.dataset_version}`",
        f"- **Git Commit:** `{report.git_commit or 'unknown'}`",
        f"- **Gate Mode:** `{report.gate_mode}`",
        f"- **Overall Gate Verdict:** `{'PASSED' if report.gate.passed else 'FAILED'}`",
        "",
        "## Leaderboard",
        "",
        "| System | Version | EM exact | EM casefold | CER | WER | ONER | UNER | Entity |",
        "|---|:---:|---:|---:|---:|---:|---:|---:|---:|",
    ]

    for res in report.results:
        agg = res.aggregate
        lines.append(
            f"| `{res.system_id}` | `{res.system_version or 'in-repo'}` | "
            f"{format_val(agg['exact_match'].score)} | "
            f"{format_val(agg['exact_match_casefold'].score)} | "
            f"{format_val(agg['cer'].score, False)} | "
            f"{format_val(agg['wer'].score, False)} | "
            f"{format_val(agg['oner'].score)} | "
            f"{format_val(agg['uner'].score)} | "
            f"{format_val(agg['entity_preservation'].score)} |"
        )

    lines.extend([
        "",
        "## Gate Evaluation",
        "",
        "| Slice | Criterion | Threshold | Observed | Eligible Tokens | Status | Reason |",
        "|---|:---:|---:|---:|---:|:---:|---|",
    ])

    for check in report.gate.checks:
        status = "PASSED" if check.passed else "**FAILED**"
        obs = f"{check.observed:.4f}" if check.observed is not None else "N/A"
        thresh = f"{check.threshold:.4f}"
        elig = str(int(check.eligible)) if check.eligible is not None else "N/A"
        lines.append(
            f"| `{check.slice_name}` | `{check.criterion}` | {thresh} | {obs} | {elig} | {status} | {check.reason or '-'} |"
        )

    lines.extend([
        "",
        "## Provenance & Dataset Hashes",
        "",
        "| Slice | Path | Rows | SHA-256 |",
        "|---|---|---:|---|",
    ])

    for ds in report.datasets:
        lines.append(f"| `{ds.slice_name}` | `{ds.path}` | {ds.rows} | `{ds.sha256[:16]}...` |")

    lines.append("")
    return "\n".join(lines)
