"""Scale-aware gatekeeper evaluating ONER, UNER, and entity preservation."""

import math

from basa_evals.core.schema import GateCheck, GateCriteria, GateResult, MetricValue, SliceConfig


def evaluate_slice_gate(
    gate: GateCriteria,
    slice_name: str,
    exploratory: bool,
    metrics: dict[str, MetricValue],
) -> list[GateCheck]:
    """Evaluate gate criteria for a single slice."""
    if exploratory:
        return []

    if slice_name not in gate.per_slice:
        return []

    slice_gate = gate.per_slice[slice_name]
    checks: list[GateCheck] = []

    # 1. ONER Check
    oner_metric = metrics.get("oner")
    if oner_metric is None or oner_metric.denominator is None or oner_metric.numerator is None:
        checks.append(
            GateCheck(
                slice_name=slice_name,
                criterion="oner",
                threshold=0.0,
                observed=None,
                eligible=None,
                passed=False,
                reason="ONER metric not available",
            )
        )
    else:
        denom = oner_metric.denominator
        if denom < gate.oner_zero_tolerance_below:
            allowed = 0
        else:
            allowed = math.ceil(gate.oner_max_rate * denom) - 1

        if slice_gate.oner_max_errors is not None:
            allowed = min(allowed, slice_gate.oner_max_errors)

        observed = oner_metric.numerator
        passed = observed <= allowed
        reason = (
            None
            if passed
            else (
                f"ON errors ({int(observed)}) exceeded allowed threshold ({allowed}) "
                f"on {int(denom)} clean tokens"
            )
        )
        checks.append(
            GateCheck(
                slice_name=slice_name,
                criterion="oner",
                threshold=float(allowed),
                observed=observed,
                eligible=denom,
                passed=passed,
                reason=reason,
            )
        )

    # 2. UNER Check
    if slice_gate.uner_max_rate is not None:
        uner_metric = metrics.get("uner")
        thresh = slice_gate.uner_max_rate
        if uner_metric is None or uner_metric.score is None:
            checks.append(
                GateCheck(
                    slice_name=slice_name,
                    criterion="uner",
                    threshold=thresh,
                    observed=None,
                    eligible=None,
                    passed=False,
                    reason="UNER metric not available",
                )
            )
        else:
            obs = uner_metric.score
            passed = obs <= thresh
            reason = None if passed else f"UNER rate ({obs:.4f}) exceeded max rate ({thresh:.4f})"
            checks.append(
                GateCheck(
                    slice_name=slice_name,
                    criterion="uner",
                    threshold=thresh,
                    observed=obs,
                    eligible=uner_metric.denominator,
                    passed=passed,
                    reason=reason,
                )
            )

    # 3. Entity Preservation Check
    if slice_gate.entity_preservation_min is not None:
        ent_metric = metrics.get("entity_preservation")
        thresh = slice_gate.entity_preservation_min
        if ent_metric is None or ent_metric.score is None:
            checks.append(
                GateCheck(
                    slice_name=slice_name,
                    criterion="entity_preservation",
                    threshold=thresh,
                    observed=None,
                    eligible=None,
                    passed=False,
                    reason="Entity preservation metric not available",
                )
            )
        else:
            obs = ent_metric.score
            passed = obs >= thresh
            reason = (
                None
                if passed
                else f"Entity preservation rate ({obs:.4f}) fell below minimum ({thresh:.4f})"
            )
            checks.append(
                GateCheck(
                    slice_name=slice_name,
                    criterion="entity_preservation",
                    threshold=thresh,
                    observed=obs,
                    eligible=ent_metric.denominator,
                    passed=passed,
                    reason=reason,
                )
            )

    return checks


def evaluate_suite_gate(
    gate: GateCriteria,
    slices: list[SliceConfig],
    slice_metrics: dict[str, dict[str, MetricValue]],
) -> GateResult:
    """Evaluate overall gate verdict across all suite slices for a target system."""
    all_checks: list[GateCheck] = []
    skipped_slices: list[str] = []

    for s_cfg in slices:
        if s_cfg.exploratory:
            skipped_slices.append(s_cfg.slice_name)
            continue
        metrics = slice_metrics.get(s_cfg.slice_name, {})
        checks = evaluate_slice_gate(
            gate,
            slice_name=s_cfg.slice_name,
            exploratory=s_cfg.exploratory,
            metrics=metrics,
        )
        all_checks.extend(checks)

    overall_passed = all(c.passed for c in all_checks) if all_checks else True
    return GateResult(
        passed=overall_passed,
        checks=all_checks,
        skipped_slices=skipped_slices,
    )
