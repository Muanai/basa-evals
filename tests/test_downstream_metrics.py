from basa_evals.metrics.downstream import (
    compute_classification_metrics,
    compute_downstream_summary,
    compute_sample_outcome,
)


def test_compute_classification_metrics_closed_form() -> None:
    gold = ["positive", "positive", "neutral", "negative", "negative"]
    pred = ["positive", "neutral", "neutral", "negative", "positive"]
    classes = ["positive", "neutral", "negative"]

    metrics = compute_classification_metrics(gold, pred, classes)
    # positive: TP=1, FP=1, FN=1 -> P=0.5, R=0.5, F1=0.5
    # neutral:  TP=1, FP=1, FN=0 -> P=0.5, R=1.0, F1=0.6667
    # negative: TP=1, FP=0, FN=1 -> P=1.0, R=0.5, F1=0.6667
    # Accuracy: 3 / 5 = 0.60
    assert round(metrics.accuracy, 4) == 0.6000
    assert round(metrics.macro_f1, 4) == round((0.5 + (2 / 3) + (2 / 3)) / 3, 4)
    assert metrics.confusion_matrix["positive"]["positive"] == 1
    assert metrics.confusion_matrix["positive"]["neutral"] == 1
    assert metrics.sample_count == 5


def test_division_by_zero_safety() -> None:
    # Model predicts only positive for all items
    gold = ["neutral", "neutral"]
    pred = ["positive", "positive"]
    classes = ["positive", "neutral", "negative"]

    metrics = compute_classification_metrics(gold, pred, classes)
    assert metrics.accuracy == 0.0
    assert metrics.per_class_f1["negative"] == 0.0
    assert metrics.macro_f1 == 0.0


def test_sample_outcomes_and_summary_partition_invariant() -> None:
    assert compute_sample_outcome("positive", "negative", "positive") == "win"
    assert compute_sample_outcome("positive", "positive", "negative") == "loss"
    assert compute_sample_outcome("positive", "positive", "positive") == "neutral"
    assert compute_sample_outcome("positive", "negative", "neutral") == "neutral"

    # Test summary aggregation
    summary = compute_downstream_summary(
        system_id="basa-default",
        classifier_id="mock",
        task="sentiment",
        classes=["positive", "neutral", "negative"],
        sample_ids=["s1", "s2", "s3"],
        raw_texts=["a", "b", "c"],
        pred_texts=["a*", "b*", "c*"],
        gold_labels=["positive", "negative", "neutral"],
        raw_preds=["negative", "negative", "neutral"],
        norm_preds=["positive", "neutral", "neutral"],
    )
    assert summary.wins == 1
    assert summary.losses == 1
    assert summary.neutrals == 1
    assert summary.wins + summary.losses + summary.neutrals == summary.sample_count
    assert summary.net_win_rate == 0.0
    assert summary.sample_count == 3
