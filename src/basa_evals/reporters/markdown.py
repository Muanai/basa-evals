"""Markdown report generator with full provenance footers."""

from basa_evals.core.schema import EvaluationReport, TokenizerBenchmarkReport



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


def generate_markdown_tokenizer_report(report: TokenizerBenchmarkReport) -> str:
    """Generate Markdown representation of a TokenizerBenchmarkReport."""
    lines: list[str] = [
        f"# Multi-Tokenizer Efficiency Benchmark Report: {report.suite_name}",
        "",
        f"- **Run ID:** `{report.run_id}`",
        f"- **Timestamp:** `{report.timestamp}`",
        f"- **Python Version:** `{report.provenance.python_version}`",
        f"- **Platform:** `{report.provenance.platform_system} ({report.provenance.platform_machine})`",
        f"- **Git Commit:** `{report.provenance.git_commit or 'unknown'}`",
        "",
        "## Cross-Model Efficiency Matrix",
        "",
        "| System | Tokenizer | Tokens (Pred / Raw) | Savings (%) | Macro CR | Raw SFI | Pred SFI | ΔSFI |",
        "|---|---|---:|---:|---:|---:|---:|---:|",
    ]

    for res in report.results:
        savings_pct = res.net_savings_rate * 100
        sign = "+" if savings_pct > 0 else ""
        dsfi_sign = "+" if res.mean_delta_sfi > 0 else ""
        lines.append(
            f"| `{res.system_id}` | `{res.tokenizer_id}` | "
            f"{res.total_pred_tokens} / {res.total_raw_tokens} | "
            f"{sign}{savings_pct:.1f}% | "
            f"{res.macro_compression_ratio:.3f}x | "
            f"{res.mean_raw_sfi:.2f} | "
            f"{res.mean_pred_sfi:.2f} | "
            f"{dsfi_sign}{res.mean_delta_sfi:.2f} |"
        )

    lines.extend([
        "",
        "## Phenomenological Slice Breakdown (Savings vs. Inflation)",
        "",
        "| System | Slice | Tokenizer | Tokens (Pred / Raw) | Savings (%) | ΔSFI | Winners / Losers / Neutral |",
        "|---|---|---|---:|---:|---:|:---:|",
    ])

    for res in report.results:
        for slice_name, s_summary in sorted(res.slice_breakdowns.items()):
            s_pct = s_summary.net_savings_rate * 100
            s_sign = "+" if s_pct > 0 else ""
            lines.append(
                f"| `{res.system_id}` | `{slice_name}` | `{res.tokenizer_id}` | "
                f"{s_summary.total_pred_tokens} / {s_summary.total_raw_tokens} | "
                f"{s_sign}{s_pct:.1f}% | "
                f"{s_summary.delta_sfi:+.2f} | "
                f"{s_summary.compression_count}W / {s_summary.inflation_count}L / {s_summary.neutral_count}N |"
            )

    lines.append("")
    return "\n".join(lines)


class MarkdownReporter:
    """Markdown report generator wrapper."""

    @staticmethod
    def render_report(report: EvaluationReport) -> str:
        """Render standard intrinsic evaluation report."""
        return generate_markdown_report(report)

    @staticmethod
    def render_tokenizer_benchmark(report: TokenizerBenchmarkReport) -> str:
        """Render multi-tokenizer benchmark report."""
        return generate_markdown_tokenizer_report(report)

