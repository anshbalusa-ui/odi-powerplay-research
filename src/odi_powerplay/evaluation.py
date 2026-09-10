"""Dependency-light prediction metrics and match-cluster bootstrap intervals."""

from __future__ import annotations

import math
import random
from collections import defaultdict
from typing import Any, Iterable, Sequence


PROBABILITY_EPSILON = 1e-15


def _validate_predictions(labels: Sequence[int], probabilities: Sequence[float]) -> None:
    if len(labels) != len(probabilities) or not labels:
        raise ValueError("Labels and probabilities must have the same nonzero length")
    if any(label not in {0, 1} for label in labels):
        raise ValueError("Labels must be binary")
    if any(not 0.0 <= probability <= 1.0 for probability in probabilities):
        raise ValueError("Probabilities must be between 0 and 1")


def roc_auc(labels: Sequence[int], probabilities: Sequence[float]) -> float:
    """Calculate ROC AUC using average ranks for tied probabilities."""

    _validate_predictions(labels, probabilities)
    positives = sum(labels)
    negatives = len(labels) - positives
    if positives == 0 or negatives == 0:
        raise ValueError("ROC AUC requires both outcome classes")

    ordered = sorted(enumerate(probabilities), key=lambda item: item[1])
    rank_sum_positive = 0.0
    position = 0
    while position < len(ordered):
        end = position + 1
        while end < len(ordered) and ordered[end][1] == ordered[position][1]:
            end += 1
        average_rank = ((position + 1) + end) / 2.0
        rank_sum_positive += sum(labels[index] * average_rank for index, _ in ordered[position:end])
        position = end
    return (rank_sum_positive - positives * (positives + 1) / 2.0) / (positives * negatives)


def compute_metrics(labels: Sequence[int], probabilities: Sequence[float]) -> dict[str, float]:
    """Return discrimination, proper scoring, and threshold metrics."""

    _validate_predictions(labels, probabilities)
    clipped = [
        min(1.0 - PROBABILITY_EPSILON, max(PROBABILITY_EPSILON, probability))
        for probability in probabilities
    ]
    brier = sum((probability - label) ** 2 for label, probability in zip(labels, probabilities))
    log_loss = -sum(
        label * math.log(probability) + (1 - label) * math.log(1 - probability)
        for label, probability in zip(labels, clipped)
    )
    accuracy = sum(
        (probability >= 0.5) == bool(label) for label, probability in zip(labels, probabilities)
    )
    return {
        "roc_auc": roc_auc(labels, probabilities),
        "log_loss": log_loss / len(labels),
        "brier_score": brier / len(labels),
        "accuracy_at_0_5": accuracy / len(labels),
    }


def calibration_coefficients(
    labels: Sequence[int],
    probabilities: Sequence[float],
    *,
    max_iterations: int = 100,
    tolerance: float = 1e-10,
) -> dict[str, float | None]:
    """Fit outcome ~ intercept + slope * logit(probability) by Newton updates."""

    _validate_predictions(labels, probabilities)
    logits = [
        math.log(clipped / (1.0 - clipped))
        for probability in probabilities
        for clipped in [min(1.0 - PROBABILITY_EPSILON, max(PROBABILITY_EPSILON, probability))]
    ]
    if max(logits) - min(logits) < tolerance:
        return {"calibration_intercept": None, "calibration_slope": None}

    intercept = 0.0
    slope = 1.0
    for _ in range(max_iterations):
        means = []
        for logit in logits:
            linear = intercept + slope * logit
            if linear >= 0:
                means.append(1.0 / (1.0 + math.exp(-linear)))
            else:
                exponential = math.exp(linear)
                means.append(exponential / (1.0 + exponential))
        weights = [max(mean * (1.0 - mean), 1e-12) for mean in means]
        gradient_intercept = sum(label - mean for label, mean in zip(labels, means))
        gradient_slope = sum(
            (label - mean) * logit for label, mean, logit in zip(labels, means, logits)
        )
        information_intercept = sum(weights)
        information_cross = sum(weight * logit for weight, logit in zip(weights, logits))
        information_slope = sum(weight * logit * logit for weight, logit in zip(weights, logits))
        determinant = information_intercept * information_slope - information_cross**2
        if determinant <= 1e-12:
            return {"calibration_intercept": None, "calibration_slope": None}
        delta_intercept = (
            information_slope * gradient_intercept - information_cross * gradient_slope
        ) / determinant
        delta_slope = (
            -information_cross * gradient_intercept + information_intercept * gradient_slope
        ) / determinant
        intercept += delta_intercept
        slope += delta_slope
        if max(abs(delta_intercept), abs(delta_slope)) < tolerance:
            break
    return {
        "calibration_intercept": intercept,
        "calibration_slope": slope,
    }


def calibration_table(
    labels: Sequence[int],
    probabilities: Sequence[float],
    *,
    bins: int = 10,
) -> list[dict[str, float | int]]:
    """Create fixed-width reliability bins without fitting on validation outcomes."""

    _validate_predictions(labels, probabilities)
    if bins < 2:
        raise ValueError("At least two calibration bins are required")
    grouped: dict[int, list[tuple[int, float]]] = defaultdict(list)
    for label, probability in zip(labels, probabilities):
        index = min(bins - 1, int(probability * bins))
        grouped[index].append((label, probability))
    return [
        {
            "bin": index,
            "lower_bound": index / bins,
            "upper_bound": (index + 1) / bins,
            "count": len(values),
            "mean_probability": sum(value[1] for value in values) / len(values),
            "observed_rate": sum(value[0] for value in values) / len(values),
        }
        for index, values in sorted(grouped.items())
    ]


def cluster_bootstrap_calibration(
    predictions: Iterable[dict[str, Any]],
    *,
    bins: int = 10,
    repetitions: int = 2000,
    seed: int = 20250905,
) -> list[dict[str, float | int]]:
    """Attach whole-match bootstrap intervals to fixed-width calibration bins."""

    materialized = list(predictions)
    labels = [int(row["label"]) for row in materialized]
    probabilities = [float(row["probability"]) for row in materialized]
    cluster_ids = [str(row["match_id"]) for row in materialized]
    point = calibration_table(labels, probabilities, bins=bins)
    samples: dict[int, list[float]] = {int(row["bin"]): [] for row in point}
    random_generator = random.Random(seed)
    for _ in range(repetitions):
        indices = draw_cluster_indices(cluster_ids, random_generator=random_generator)
        sample_table = calibration_table(
            [labels[index] for index in indices],
            [probabilities[index] for index in indices],
            bins=bins,
        )
        for row in sample_table:
            index = int(row["bin"])
            if index in samples:
                samples[index].append(float(row["observed_rate"]))
    return [
        {
            **row,
            "observed_rate_lower_95": _percentile(samples[int(row["bin"])], 0.025),
            "observed_rate_upper_95": _percentile(samples[int(row["bin"])], 0.975),
            "bootstrap_repetitions_valid": len(samples[int(row["bin"])]),
        }
        for row in point
    ]


def draw_cluster_indices(
    cluster_ids: Sequence[str], *, random_generator: random.Random
) -> list[int]:
    """Sample matches with replacement while retaining every innings row in each draw."""

    indices_by_cluster: dict[str, list[int]] = defaultdict(list)
    for index, cluster_id in enumerate(cluster_ids):
        indices_by_cluster[str(cluster_id)].append(index)
    clusters = sorted(indices_by_cluster)
    if not clusters:
        raise ValueError("At least one cluster is required")
    sampled = [random_generator.choice(clusters) for _ in clusters]
    return [index for cluster_id in sampled for index in indices_by_cluster[cluster_id]]


def _percentile(values: Sequence[float], probability: float) -> float:
    ordered = sorted(values)
    position = (len(ordered) - 1) * probability
    lower = math.floor(position)
    upper = math.ceil(position)
    if lower == upper:
        return ordered[lower]
    return ordered[lower] + (ordered[upper] - ordered[lower]) * (position - lower)


def cluster_bootstrap_metrics(
    predictions: Iterable[dict[str, Any]],
    *,
    repetitions: int = 2000,
    seed: int = 20250905,
) -> dict[str, Any]:
    """Return match-clustered percentile intervals for core validation metrics."""

    materialized = list(predictions)
    if repetitions < 1:
        raise ValueError("repetitions must be positive")
    labels = [int(row["label"]) for row in materialized]
    probabilities = [float(row["probability"]) for row in materialized]
    cluster_ids = [str(row["match_id"]) for row in materialized]
    point = {
        **compute_metrics(labels, probabilities),
        **calibration_coefficients(labels, probabilities),
    }
    samples: dict[str, list[float]] = {metric: [] for metric in point}
    failed = 0
    random_generator = random.Random(seed)

    for _ in range(repetitions):
        indices = draw_cluster_indices(cluster_ids, random_generator=random_generator)
        sample_labels = [labels[index] for index in indices]
        sample_probabilities = [probabilities[index] for index in indices]
        try:
            metrics = {
                **compute_metrics(sample_labels, sample_probabilities),
                **calibration_coefficients(sample_labels, sample_probabilities),
            }
        except ValueError:
            failed += 1
            continue
        for metric, value in metrics.items():
            if value is not None:
                samples[metric].append(value)

    if any(not samples[metric] for metric, value in point.items() if value is not None):
        raise ValueError("No valid bootstrap samples contained both classes")
    intervals = {
        metric: {
            "estimate": point[metric],
            "lower_95": _percentile(values, 0.025) if values else None,
            "upper_95": _percentile(values, 0.975) if values else None,
        }
        for metric, values in samples.items()
    }
    return {
        "repetitions_requested": repetitions,
        "repetitions_valid": repetitions - failed,
        "repetitions_failed": failed,
        "seed": seed,
        "metrics": intervals,
    }
