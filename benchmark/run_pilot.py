"""Benchmark runner script for direct invocation."""

import sys

from basa_evals.core.loader import load_suite
from basa_evals.core.runner import EvaluationRunner
from basa_evals.reporters.console import print_evaluation_summary
from basa_evals.reporters.exporter import append_findings_log, export_json


def main() -> None:
    suite_cfg, slices_data = load_suite("pilot_210")
    runner = EvaluationRunner(suite_cfg, slices_data=slices_data)
    report = runner.run()

    print_evaluation_summary(report)
    out_file = export_json(report)
    findings_file = append_findings_log(report, "docs/findings/m1-baseline.md", slices_data)

    print(f"Artifact: {out_file}")
    print(f"Findings: {findings_file}")
    sys.exit(0 if report.gate.passed else 1)


if __name__ == "__main__":
    main()
