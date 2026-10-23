from typing import Literal

from basa_evals.core.schema import (
    ClassificationMetrics,
    DownstreamTaskSummary,
    SampleClassificationResult,
)


def compute_classification_metrics(
    gold_labels: list[str],
    pred_labels: list[str],
    classes: list[str],
) -> ClassificationMetrics:
    """Compute multi-class accuracy, precision, recall, macro F1, and confusion matrix."""
    if len(gold_labels) != len(pred_labels):
        raise ValueError(
            f"Length mismatch between gold ({len(gold_labels)}) and pred ({len(pred_labels)}) labels."
        )

    n_samples = len(gold_labels)
    if n_samples == 0:
        return ClassificationMetrics(
            macro_f1=0.0,
            weighted_f1=0.0,
            accuracy=0.0,
            precision_macro=0.0,
            recall_macro=0.0,
            per_class_f1={c: 0.0 for c in classes},
            confusion_matrix={c1: {c2: 0 for c2 in classes} for c1 in classes},
            sample_count=0,
        )

    # Initialize confusion matrix: rows = gold, columns = pred
    cm: dict[str, dict[str, int]] = {c1: {c2: 0 for c2 in classes} for c1 in classes}
    for g, p in zip(gold_labels, pred_labels, strict=True):
        if g in cm and p in cm[g]:
            cm[g][p] += 1
        elif g in cm:
            # Predicted class outside configured classes
            pass

    per_class_p: dict[str, float] = {}
    per_class_r: dict[str, float] = {}
    per_class_f1: dict[str, float] = {}
    per_class_support: dict[str, int] = {}

    total_tp = 0
    for c in classes:
        tp = cm[c].get(c, 0)
        total_tp += tp
        fp = sum(cm[other].get(c, 0) for other in classes if other != c)
        fn = sum(cm[c].get(other, 0) for other in classes if other != c)
        support = sum(cm[c].values())
        per_class_support[c] = support

        prec = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        rec = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        f1 = (2 * prec * rec) / (prec + rec) if (prec + rec) > 0 else 0.0

        per_class_p[c] = prec
        per_class_r[c] = rec
        per_class_f1[c] = f1

    accuracy = total_tp / n_samples if n_samples > 0 else 0.0
    macro_f1 = sum(per_class_f1.values()) / len(classes) if classes else 0.0
    precision_macro = sum(per_class_p.values()) / len(classes) if classes else 0.0
    recall_macro = sum(per_class_r.values()) / len(classes) if classes else 0.0

    weighted_f1 = (
        sum(per_class_support[c] * per_class_f1[c] for c in classes) / n_samples
        if n_samples > 0
        else 0.0
    )

    return ClassificationMetrics(
        macro_f1=macro_f1,
        weighted_f1=weighted_f1,
        accuracy=accuracy,
        precision_macro=precision_macro,
        recall_macro=recall_macro,
        per_class_f1=per_class_f1,
        confusion_matrix=cm,
        sample_count=n_samples,
    )


def compute_sample_outcome(
    gold: str,
    raw_pred: str,
    norm_pred: str,
) -> Literal["win", "loss", "neutral"]:
    """Partition a sample into Win, Loss, or Neutral under normalization."""
    raw_correct = raw_pred == gold
    norm_correct = norm_pred == gold

    if not raw_correct and norm_correct:
        return "win"
    if raw_correct and not norm_correct:
        return "loss"
    return "neutral"


def compute_downstream_summary(
    system_id: str,
    classifier_id: str,
    task: str,
    classes: list[str],
    sample_ids: list[str],
    raw_texts: list[str],
    pred_texts: list[str],
    gold_labels: list[str],
    raw_preds: list[str],
    norm_preds: list[str],
) -> DownstreamTaskSummary:
    """Compute task summary comparing raw vs normalized predictions across a sample set."""
    n_samples = len(sample_ids)
    raw_metrics = compute_classification_metrics(gold_labels, raw_preds, classes)
    norm_metrics = compute_classification_metrics(gold_labels, norm_preds, classes)

    sample_results: list[SampleClassificationResult] = []
    wins = 0
    losses = 0
    neutrals = 0

    for s_id, raw_t, pred_t, gold, r_pred, n_pred in zip(
        sample_ids, raw_texts, pred_texts, gold_labels, raw_preds, norm_preds, strict=True
    ):
        outcome = compute_sample_outcome(gold, r_pred, n_pred)
        if outcome == "win":
            wins += 1
        elif outcome == "loss":
            losses += 1
        else:
            neutrals += 1

        sample_results.append(
            SampleClassificationResult(
                sample_id=s_id,
                raw_text=raw_t,
                pred_text=pred_t,
                gold_label=gold,
                raw_pred_label=r_pred,
                norm_pred_label=n_pred,
                outcome=outcome,
            )
        )

    delta_f1 = norm_metrics.macro_f1 - raw_metrics.macro_f1
    delta_accuracy = norm_metrics.accuracy - raw_metrics.accuracy
    net_win_rate = (wins - losses) / n_samples if n_samples > 0 else 0.0

    return DownstreamTaskSummary(
        system_id=system_id,
        classifier_id=classifier_id,
        task=task,
        sample_count=n_samples,
        raw_metrics=raw_metrics,
        norm_metrics=norm_metrics,
        delta_f1=delta_f1,
        delta_accuracy=delta_accuracy,
        wins=wins,
        losses=losses,
        neutrals=neutrals,
        net_win_rate=net_win_rate,
        sample_results=sample_results,
    )
