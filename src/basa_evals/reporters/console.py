"""Console visualizer using Rich tables and formatting."""

from rich.console import Console
from rich.table import Table

from basa_evals.core.schema import EvaluationReport, TokenizerBenchmarkReport



def format_metric(val: float | None, as_pct: bool = True) -> str:
    """Format a metric float into a percentage or decimal string."""
    if val is None:
        return "N/A"
    return f"{val * 100:.1f}%" if as_pct else f"{val:.4f}"


def print_evaluation_summary(report: EvaluationReport, console: Console | None = None) -> None:
    """Print high-level leaderboard and gate check results to console."""
    if console is None:
        console = Console()

    # 1. Main Leaderboard Table
    table = Table(
        title=f"BASA Evals — Leaderboard ({report.run_name})",
        header_style="bold magenta",
        show_header=True,
    )
    table.add_column("System", style="bold", no_wrap=True)
    table.add_column("Version", justify="center")
    table.add_column("EM exact", justify="right")
    table.add_column("EM casefold", justify="right")
    table.add_column("CER", justify="right")
    table.add_column("WER", justify="right")
    table.add_column("ONER", justify="right")
    table.add_column("UNER", justify="right")
    table.add_column("Entity", justify="right")

    for res in report.results:
        agg = res.aggregate
        em_ex = agg.get("exact_match")
        em_cf = agg.get("exact_match_casefold")
        cer = agg.get("cer")
        wer = agg.get("wer")
        oner = agg.get("oner")
        uner = agg.get("uner")
        ent = agg.get("entity_preservation")

        # Color rules:
        # EM below 50% amber
        em_ex_str = format_metric(em_ex.score if em_ex else None)
        if em_ex and em_ex.score is not None and em_ex.score < 0.5:
            em_ex_str = f"[yellow]{em_ex_str}[/yellow]"

        em_cf_str = format_metric(em_cf.score if em_cf else None)
        if em_cf and em_cf.score is not None and em_cf.score < 0.5:
            em_cf_str = f"[yellow]{em_cf_str}[/yellow]"

        # ONER: non-zero is highlighted in red/amber (never green alone)
        oner_str = format_metric(oner.score if oner else None)
        if oner and oner.score is not None and oner.score > 0.0:
            oner_str = f"[red]{oner_str}[/red]"

        table.add_row(
            res.system_id,
            res.system_version or "in-repo",
            em_ex_str,
            em_cf_str,
            format_metric(cer.score if cer else None, as_pct=False),
            format_metric(wer.score if wer else None, as_pct=False),
            oner_str,
            format_metric(uner.score if uner else None),
            format_metric(ent.score if ent else None),
        )

    console.print()
    console.print(table)

    # 2. Gate Checks Table
    gate_table = Table(
        title=f"Gate Verdict: {'[bold green]PASSED[/bold green]' if report.gate.passed else '[bold red]FAILED[/bold red]'} (Mode: {report.gate_mode})",
        header_style="bold blue",
    )
    gate_table.add_column("Slice", style="bold")
    gate_table.add_column("Criterion", justify="center")
    gate_table.add_column("Threshold", justify="right")
    gate_table.add_column("Observed", justify="right")
    gate_table.add_column("Eligible Tokens", justify="right")
    gate_table.add_column("Status", justify="center")
    gate_table.add_column("Details", justify="left")

    for check in report.gate.checks:
        status = "[green]PASS[/green]" if check.passed else "[red]FAIL[/red]"
        obs_str = f"{check.observed:.4f}" if check.observed is not None else "N/A"
        thresh_str = f"{check.threshold:.4f}"
        elig_str = str(int(check.eligible)) if check.eligible is not None else "N/A"
        gate_table.add_row(
            check.slice_name,
            check.criterion,
            thresh_str,
            obs_str,
            elig_str,
            status,
            check.reason or "-",
        )

    console.print()
    console.print(gate_table)
    console.print()


def print_tokenizer_benchmark(
    report: TokenizerBenchmarkReport,
    console: Console | None = None,
) -> None:
    """Print multi-tokenizer efficiency benchmark matrix and slice breakdown to console."""
    if console is None:
        console = Console()

    # 1. Main System x Tokenizer Leaderboard
    table = Table(
        title=f"Tier 2: Multi-Tokenizer Efficiency Benchmark ({report.suite_name})",
        header_style="bold magenta",
        show_header=True,
    )
    table.add_column("System", style="bold", no_wrap=True)
    table.add_column("Tokenizer", style="cyan")
    table.add_column("Tokens (Pred / Raw)", justify="right")
    table.add_column("Savings (%)", justify="right")
    table.add_column("Macro CR", justify="right")
    table.add_column("Raw SFI", justify="right")
    table.add_column("Pred SFI", justify="right")
    table.add_column("ΔSFI", justify="right")

    for res in report.results:
        # Savings formatting
        savings_pct = res.net_savings_rate * 100
        if savings_pct > 0.05:
            savings_str = f"[green]+{savings_pct:.1f}%[/green]"
        elif savings_pct < -0.05:
            savings_str = f"[red]{savings_pct:.1f}%[/red]"
        else:
            savings_str = f"[dim]{savings_pct:.1f}%[/dim]"

        # SFI delta formatting
        if res.mean_delta_sfi > 0.05:
            dsfi_str = f"[green]+{res.mean_delta_sfi:.2f}[/green]"
        elif res.mean_delta_sfi < -0.05:
            dsfi_str = f"[red]{res.mean_delta_sfi:.2f}[/red]"
        else:
            dsfi_str = f"[dim]{res.mean_delta_sfi:.2f}[/dim]"

        table.add_row(
            res.system_id,
            res.tokenizer_id,
            f"{res.total_pred_tokens} / {res.total_raw_tokens}",
            savings_str,
            f"{res.macro_compression_ratio:.3f}x",
            f"{res.mean_raw_sfi:.2f}",
            f"{res.mean_pred_sfi:.2f}",
            dsfi_str,
        )

    console.print()
    console.print(table)

    # 2. Slice Breakdown Table
    slice_table = Table(
        title="Phenomenological Slice Trade-Offs (Savings vs. Inflation)",
        header_style="bold blue",
    )
    slice_table.add_column("System", style="bold")
    slice_table.add_column("Slice")
    slice_table.add_column("Tokenizer", style="cyan")
    slice_table.add_column("Tokens (Pred / Raw)", justify="right")
    slice_table.add_column("Savings (%)", justify="right")
    slice_table.add_column("ΔSFI", justify="right")
    slice_table.add_column("Wins / Losses / Neutral", justify="center")

    for res in report.results:
        for slice_name, s_summary in sorted(res.slice_breakdowns.items()):
            s_pct = s_summary.net_savings_rate * 100
            if s_pct > 0.05:
                s_str = f"[green]+{s_pct:.1f}%[/green]"
            elif s_pct < -0.05:
                s_str = f"[red]{s_pct:.1f}%[/red]"
            else:
                s_str = f"[dim]{s_pct:.1f}%[/dim]"

            ratio_counts = (
                f"[green]{s_summary.compression_count}W[/green] / "
                f"[red]{s_summary.inflation_count}L[/red] / "
                f"[dim]{s_summary.neutral_count}N[/dim]"
            )

            slice_table.add_row(
                res.system_id,
                slice_name,
                res.tokenizer_id,
                f"{s_summary.total_pred_tokens} / {s_summary.total_raw_tokens}",
                s_str,
                f"{s_summary.delta_sfi:+.2f}",
                ratio_counts,
            )

    console.print()
    console.print(slice_table)
    console.print()


class ConsoleReporter:
    """Rich console visualizer wrapper."""

    def __init__(self, console: Console | None = None) -> None:
        self.console = console or Console()

    def render_summary(self, report: EvaluationReport) -> None:
        """Render standard intrinsic evaluation report."""
        print_evaluation_summary(report, self.console)

    def render_tokenizer_benchmark(self, report: TokenizerBenchmarkReport) -> None:
        """Render multi-tokenizer benchmark report."""
        print_tokenizer_benchmark(report, self.console)

