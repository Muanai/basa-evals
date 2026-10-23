"""Command-line interface for the BASA Evals framework."""

import json
from pathlib import Path

import typer
from rich.console import Console
from rich.table import Table

from basa_evals.core.loader import load_suite, resolve_suite_path
from basa_evals.core.registry import Registry
from basa_evals.core.runner import EvaluationRunner
from basa_evals.core.schema import EvaluationReport, Sample
from basa_evals.reporters.console import print_evaluation_summary
from basa_evals.reporters.exporter import append_findings_log, export_json

app = typer.Typer(
    name="basa-eval",
    help="Independent evaluation framework for Indonesian NLP preprocessing and text normalization.",
    no_args_is_help=True,
)
console = Console()


@app.command()
def run(
    suite: str = typer.Option(
        "pilot_210", "--suite", "-s", help="Suite name or path to suite YAML"
    ),
    system: str | None = typer.Option(
        None, "--system", help="Filter execution to a specific system ID"
    ),
    output: Path | None = typer.Option(
        None, "--output", "-o", help="Path to write JSON run artifact"
    ),
    findings: Path | None = typer.Option(
        None, "--findings", help="Path to append corrupted token findings"
    ),
    no_gate: bool = typer.Option(
        False, "--no-gate", help="Run in advisory mode without failing gate exit code"
    ),
) -> None:
    """Execute an evaluation suite and print leaderboard and gate verdict."""
    try:
        suite_path = resolve_suite_path(suite)
        suite_cfg, slices_data = load_suite(suite_path)
    except Exception as e:
        console.print(f"[bold red]Configuration/Loading Error:[/bold red] {e}")
        raise typer.Exit(code=2) from e

    if system:
        matching = [s for s in suite_cfg.systems if s.system_id == system]
        if not matching:
            console.print(
                f"[bold red]Error:[/bold red] System '{system}' not found in suite configuration."
            )
            raise typer.Exit(code=2)
        suite_cfg.systems = matching

    try:
        runner = EvaluationRunner(suite_cfg, slices_data=slices_data, target_system=system)
        report = runner.run(no_gate=no_gate, target_system=system)
    except Exception as e:
        console.print(f"[bold red]Execution Error:[/bold red] {e}")
        raise typer.Exit(code=2) from e

    # 1. Console leaderboard output
    print_evaluation_summary(report, console=console)

    # 2. Export JSON artifact
    out_file = export_json(report, output_path=output)
    console.print(f"[dim]Run artifact written to: {out_file}[/dim]")

    # 3. Optional findings log append
    if findings:
        findings_file = append_findings_log(report, findings, slices_data)
        console.print(f"[dim]Findings logged to: {findings_file}[/dim]")

    # 4. Exit code logic
    if report.gate.passed or no_gate:
        raise typer.Exit(code=0)
    else:
        raise typer.Exit(code=1)


@app.command("list-suites")
def list_suites() -> None:
    """List all available benchmark suite configurations."""
    table = Table(title="Available Evaluation Suites", header_style="bold green")
    table.add_column("Suite Name", style="bold")
    table.add_column("Location", style="dim")

    found: set[str] = set()
    # Check configs/suites
    configs_dir = Path("configs/suites")
    if configs_dir.is_dir():
        for f in configs_dir.glob("*.yaml"):
            found.add(f.stem)
            table.add_row(f.stem, str(f))

    # Check packaged suites
    pkg_suites = Path(__file__).parent / "configs" / "suites"
    if pkg_suites.is_dir():
        for f in pkg_suites.glob("*.yaml"):
            if f.stem not in found:
                table.add_row(f.stem, str(f))

    console.print(table)


@app.command("list-systems")
def list_systems() -> None:
    """List registered SUT adapters and their runtime availability."""
    table = Table(title="Registered SUT Adapters", header_style="bold cyan")
    table.add_column("Adapter Key", style="bold")
    table.add_column("Status", justify="center")
    table.add_column("Version", justify="center")
    table.add_column("Note", justify="left")

    for key in Registry.available_keys():
        try:
            adapter = Registry.get(key)
            status = "[green]Available[/green]"
            ver = adapter.version or "in-repo"
            note = "Ready"
        except ImportError as e:
            status = "[yellow]Missing Extra[/yellow]"
            ver = "N/A"
            note = str(e)
        except Exception as e:
            status = "[red]Error[/red]"
            ver = "N/A"
            note = str(e)

        table.add_row(key, status, ver, note)

    console.print(table)


@app.command("validate-dataset")
def validate_dataset(
    slice_name: str | None = typer.Option(None, "--slice", help="Specific slice to validate"),
) -> None:
    """Validate dataset slices against schema constraints and integrity rules."""

    repo_root = Path.cwd()
    data_dir = repo_root / "data"
    if not data_dir.is_dir():
        data_dir = Path(__file__).parent / "data"

    files = list(data_dir.rglob("*.jsonl"))
    if not files:
        console.print("[bold red]No dataset JSONL files found.[/bold red]")
        raise typer.Exit(code=2)

    total_samples = 0
    errors: list[str] = []

    for file_path in files:
        if slice_name and slice_name not in file_path.name:
            continue

        with open(file_path, encoding="utf-8") as f:
            for line_no, line in enumerate(f, 1):
                line = line.strip()
                if not line:
                    continue
                try:
                    Sample.model_validate(json.loads(line))
                    total_samples += 1
                except Exception as e:
                    errors.append(f"{file_path.name}:{line_no} — {e}")

    if errors:
        console.print(f"[bold red]Found {len(errors)} validation errors:[/bold red]")
        for err in errors[:10]:
            console.print(f"  • {err}")
        if len(errors) > 10:
            console.print(f"  ... and {len(errors) - 10} more.")
        raise typer.Exit(code=1)
    else:
        console.print(
            f"[bold green]Dataset integrity verified: {total_samples} samples valid.[/bold green]"
        )


@app.command()
def inspect(
    run_file: Path = typer.Argument(..., help="Path to JSON run artifact"),
    slice: str | None = typer.Option(None, "--slice", help="Filter by slice name"),
) -> None:
    """Inspect a previously generated JSON run artifact."""
    if not run_file.is_file():
        console.print(f"[bold red]File not found:[/bold red] {run_file}")
        raise typer.Exit(code=2)

    with open(run_file, encoding="utf-8") as f:
        data = json.load(f)

    report = EvaluationReport.model_validate(data)
    print_evaluation_summary(report, console=console)


@app.command(name="list-tokenizers")
def list_tokenizers() -> None:
    """List available subword tokenizers and backend library availability."""
    from basa_evals.tokenizers.registry import TokenizerRegistry

    registry = TokenizerRegistry()
    registry.register_defaults()

    table = Table(
        title="Available Subword Tokenizers (Tier 2)",
        header_style="bold magenta",
        show_header=True,
    )
    table.add_column("Tokenizer ID", style="bold cyan")
    table.add_column("Family", justify="center")
    table.add_column("Status / Backend")

    try:
        import tiktoken  # type: ignore[import-not-found]  # noqa: F401

        has_tiktoken = True
    except ImportError:
        has_tiktoken = False

    try:
        import transformers  # type: ignore[import-not-found]  # noqa: F401

        has_transformers = True
    except ImportError:
        has_transformers = False



    for tok_id in registry.list_available():
        if tok_id == "mock-subword":
            status = "[green]Ready (Built-in offline mock)[/green]"
            family = "mock"
        elif tok_id in ("gpt-4o", "llama-3"):
            if has_tiktoken or has_transformers:
                status = "[green]Ready[/green]"
            else:
                status = "[yellow]Requires `pip install basa-evals[tokenizers]` (tiktoken)[/yellow]"
            family = "bpe"
        elif tok_id == "indobert":
            if has_transformers:
                status = "[green]Ready (IndoBERT WordPiece)[/green]"
            else:
                status = (
                    "[yellow]Requires `pip install basa-evals[tokenizers]` (transformers)[/yellow]"
                )
            family = "wordpiece"
        elif tok_id == "gemma-2":
            if has_transformers:
                status = "[green]Ready (Gemma SentencePiece)[/green]"
            else:
                status = (
                    "[yellow]Requires `pip install basa-evals[tokenizers]` (transformers)[/yellow]"
                )
            family = "sentencepiece"
        else:
            status = "[green]Registered[/green]"
            family = "custom"

        table.add_row(tok_id, family, status)

    console.print()
    console.print(table)
    console.print()


@app.command(name="tokenize")
def tokenize(
    suite: str = typer.Option(
        "pilot_210", "--suite", "-s", help="Suite name or path to suite YAML"
    ),
    systems: str | None = typer.Option(
        None, "--systems", help="Comma-separated system IDs to evaluate"
    ),
    tokenizers: str | None = typer.Option(
        None,
        "--tokenizers",
        "-t",
        help="Comma-separated tokenizer IDs (e.g. gpt-4o,llama-3,mock-subword)",
    ),
    output_dir: Path | None = typer.Option(
        None, "--output-dir", "-o", help="Directory to write JSON and Markdown benchmark reports"
    ),
) -> None:
    """Run Tier 2 multi-tokenizer efficiency benchmark across systems and tokenizers."""
    from basa_evals.reporters.console import ConsoleReporter
    from basa_evals.reporters.markdown import MarkdownReporter
    from basa_evals.tokenizers.registry import TokenizerRegistry
    from basa_evals.tokenizers.runner import TokenizerRunner

    # 1. Load Suite and Samples
    try:
        suite_path = resolve_suite_path(suite)
        suite_cfg, slices_data = load_suite(suite_path)
    except Exception as e:
        console.print(f"[bold red]Configuration/Loading Error:[/bold red] {e}")
        raise typer.Exit(code=2) from e

    all_samples: list[Sample] = [s for _, slice_samples in slices_data for s in slice_samples]

    if not all_samples:
        console.print("[bold red]Error:[/bold red] No samples loaded from suite.")
        raise typer.Exit(code=2)

    # 2. Resolve Systems Under Test
    from basa_evals.adapters.base import BasePreprocessor
    from basa_evals.adapters.identity import RawAdapter
    from basa_evals.tokenizers.base import TokenizerAdapter

    target_sys_ids = (
        [s.strip() for s in systems.split(",")]
        if systems
        else [s.system_id for s in suite_cfg.systems]
    )
    sut_instances: list[BasePreprocessor] = []
    for sys_id in target_sys_ids:
        # Check if configured in suite
        matching = [s for s in suite_cfg.systems if s.system_id == sys_id]
        if matching:
            cfg = matching[0]
            inst = Registry.get(cfg.adapter, system_id=cfg.system_id, **cfg.params)
            sut_instances.append(inst)
        elif sys_id == "raw-identity":
            sut_instances.append(RawAdapter())
        else:
            try:
                inst = Registry.get(sys_id, system_id=sys_id)
                sut_instances.append(inst)
            except Exception as e:
                console.print(f"[bold red]Error resolving system '{sys_id}':[/bold red] {e}")
                raise typer.Exit(code=2) from e

    # 3. Resolve Tokenizers
    tok_registry = TokenizerRegistry()
    tok_registry.register_defaults()

    target_tok_ids = (
        [t.strip() for t in tokenizers.split(",")]
        if tokenizers
        else [t for t in tok_registry.list_available() if t != "mock-subword"] or ["mock-subword"]
    )

    tok_instances: list[TokenizerAdapter] = []
    for tok_id in target_tok_ids:
        try:
            tok_inst = tok_registry.get(tok_id)
            tok_instances.append(tok_inst)
        except Exception as e:
            console.print(f"[bold red]Error loading tokenizer '{tok_id}':[/bold red] {e}")
            raise typer.Exit(code=2) from e


    # 4. Run Benchmark
    console.print(
        f"[bold blue]Running Tokenizer Benchmark on {len(all_samples)} samples across "
        f"{len(sut_instances)} systems and {len(tok_instances)} tokenizers...[/bold blue]"
    )

    try:
        report = TokenizerRunner.run_benchmark(
            samples=all_samples,
            systems=sut_instances,
            tokenizers=tok_instances,
            suite_name=suite_cfg.name,
        )
    except Exception as e:
        console.print(f"[bold red]Benchmark Execution Error:[/bold red] {e}")
        raise typer.Exit(code=2) from e

    # 5. Render Console Results
    console_reporter = ConsoleReporter(console=console)
    console_reporter.render_tokenizer_benchmark(report)

    # 6. Save Reports if Output Dir Provided
    if output_dir:
        output_dir.mkdir(parents=True, exist_ok=True)
        json_file = output_dir / f"tokenizer_report_{report.run_id[:8]}.json"
        with open(json_file, "w", encoding="utf-8") as f:
            f.write(report.model_dump_json(indent=2))

        md_file = output_dir / f"tokenizer_report_{report.run_id[:8]}.md"
        with open(md_file, "w", encoding="utf-8") as f:
            f.write(MarkdownReporter.render_tokenizer_benchmark(report))

        console.print(f"[dim]Reports written to {json_file} and {md_file}[/dim]")


def main() -> None:
    """Entry point for basa-eval CLI script."""
    app()


if __name__ == "__main__":
    main()
