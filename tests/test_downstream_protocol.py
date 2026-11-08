from basa_evals.core.schema import (
    ClassificationMetrics,
    DownstreamBenchmarkReport,
    DownstreamTaskSummary,
    RunProvenance,
    SampleClassificationResult,
)


def test_downstream_schema_contracts() -> None:
    raw_m = ClassificationMetrics(
        macro_f1=0.70,
        weighted_f1=0.70,
        accuracy=0.72,
        precision_macro=0.71,
        recall_macro=0.70,
        per_class_f1={"positive": 0.8, "neutral": 0.6, "negative": 0.7},
        confusion_matrix={"positive": {"positive": 40, "neutral": 5, "negative": 5}},
        sample_count=50,
    )
    norm_m = ClassificationMetrics(
        macro_f1=0.75,
        weighted_f1=0.75,
        accuracy=0.78,
        precision_macro=0.76,
        recall_macro=0.75,
        per_class_f1={"positive": 0.85, "neutral": 0.65, "negative": 0.75},
        confusion_matrix={"positive": {"positive": 44, "neutral": 3, "negative": 3}},
        sample_count=50,
    )
    res = SampleClassificationResult(
        sample_id="s1",
        raw_text="bagus bgt",
        pred_text="bagus sekali",
        gold_label="positive",
        raw_pred_label="neutral",
        norm_pred_label="positive",
        outcome="win",
    )
    summary = DownstreamTaskSummary(
        system_id="basa-default",
        classifier_id="mock-sentiment",
        task="sentiment",
        sample_count=50,
        raw_metrics=raw_m,
        norm_metrics=norm_m,
        delta_f1=0.05,
        delta_accuracy=0.06,
        wins=5,
        losses=1,
        neutrals=44,
        net_win_rate=0.08,
        sample_results=[res],
    )
    assert summary.wins + summary.losses + summary.neutrals == summary.sample_count

    report = DownstreamBenchmarkReport(
        run_id="run-test",
        timestamp="2026-10-23T12:00:00Z",
        provenance=RunProvenance(
            git_commit="abc",
            basa_evals_version="0.1.0",
            python_version="3.12.6",
            platform_system="Windows",
            platform_machine="AMD64",
        ),
        suite_name="downstream_smsa",
        task="sentiment",
        classifier_id="mock-sentiment",
        systems=["basa-default"],
        results=[summary],
    )
    assert report.task == "sentiment"
