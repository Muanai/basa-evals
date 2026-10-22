"""Console visualizer using Rich tables and formatting."""

from rich.console import Console
from rich.table import Table
from basa_evals.core.schema import EvaluationReport, SystemResult


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
