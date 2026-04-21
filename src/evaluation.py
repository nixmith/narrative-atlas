"""
Evaluation metrics for Narrative Atlas.

Computes:
  1. Per-method classification performance (accuracy, P/R/F1) on test split
  2. Inter-method agreement (Cohen's κ) on full dataset
  3. Confusion matrices for error analysis

Usage:
    from src.evaluation import evaluate_all
    metrics = evaluate_all(scored_df, config)
"""

import pandas as pd
import numpy as np
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    cohen_kappa_score,
)


METHODS = ["vader", "logreg", "finbert"]
LABEL_ORDER = ["positive", "neutral", "negative"]


def evaluate_classifier(
    true_labels: list[str],
    predicted_labels: list[str],
    method_name: str,
) -> dict:
    """
    Evaluate a single method's classification performance.

    Args:
        true_labels: Expert-annotated ground truth labels.
        predicted_labels: Method's predicted labels.
        method_name: Name of the method (for display).

    Returns:
        Dict with:
            'method': str
            'accuracy': float
            'classification_report': dict (sklearn format, includes per-class P/R/F1)
            'confusion_matrix': np.ndarray (3x3, rows=true, cols=predicted)
    """
    acc = accuracy_score(true_labels, predicted_labels)
    report = classification_report(
        true_labels, predicted_labels,
        labels=LABEL_ORDER, output_dict=True, zero_division=0
    )
    cm = confusion_matrix(true_labels, predicted_labels, labels=LABEL_ORDER)
    return {
        "method": method_name,
        "accuracy": acc,
        "classification_report": report,
        "confusion_matrix": cm,
    }


def evaluate_agreement(
    labels_a: list[str],
    labels_b: list[str],
    name_a: str,
    name_b: str,
) -> dict:
    """
    Compute pairwise agreement between two methods.

    Args:
        labels_a: Predicted labels from method A.
        labels_b: Predicted labels from method B.
        name_a: Name of method A.
        name_b: Name of method B.

    Returns:
        Dict with:
            'pair': str (e.g., 'vader_vs_logreg')
            'agreement_pct': float (0-100)
            'cohens_kappa': float (-1 to +1)
    """
    agreement = sum(a == b for a, b in zip(labels_a, labels_b)) / len(labels_a) * 100
    kappa = cohen_kappa_score(labels_a, labels_b)
    return {
        "pair": f"{name_a}_vs_{name_b}",
        "agreement_pct": agreement,
        "cohens_kappa": kappa,
    }


def evaluate_all(df: pd.DataFrame, config: dict) -> dict:
    """
    Run all evaluations and print formatted summary.

    Args:
        df: Scored DataFrame with true_label, split, and all method columns.
        config: Loaded config dict.

    Returns:
        Nested dict:
            'classifiers': {method_name: evaluate_classifier result}
            'agreement': {pair_name: evaluate_agreement result}

    Also prints:
        - Per-method accuracy table
        - Per-method per-class F1 table
        - Pairwise agreement + κ table
    """
    results = {"classifiers": {}, "agreement": {}}
    test_df = df[df["split"] == "test"]

    for method in METHODS:
        results["classifiers"][method] = evaluate_classifier(
            test_df["true_label"].tolist(),
            test_df[f"{method}_label"].tolist(),
            method,
        )

    for i, m1 in enumerate(METHODS):
        for m2 in METHODS[i + 1:]:
            key = f"{m1}_vs_{m2}"
            results["agreement"][key] = evaluate_agreement(
                df[f"{m1}_label"].tolist(),
                df[f"{m2}_label"].tolist(),
                m1, m2,
            )

    return results


def print_summary(results: dict) -> None:
    """
    Print a clean, formatted summary of all evaluation results.

    Format:
        === Classification Performance (Test Set) ===
        Method     Accuracy   F1-macro   F1-pos   F1-neu   F1-neg
        VADER      0.XXX      0.XXX      0.XXX    0.XXX    0.XXX
        LogReg     0.XXX      0.XXX      0.XXX    0.XXX    0.XXX
        FinBERT    0.XXX      0.XXX      0.XXX    0.XXX    0.XXX

        === Inter-Method Agreement (Full Dataset) ===
        Pair                Agreement%   Cohen's κ
        VADER vs LogReg     XX.X%        0.XXX
        VADER vs FinBERT    XX.X%        0.XXX
        LogReg vs FinBERT   XX.X%        0.XXX
    """
    print("\n" + "=" * 62)
    print("Classification Performance (Test Set)")
    print("=" * 62)
    print(f"{'Method':<10} {'Accuracy':>10} {'F1-macro':>10} {'F1-pos':>10} {'F1-neu':>10} {'F1-neg':>10}")
    print("-" * 62)
    for method in METHODS:
        r = results["classifiers"][method]
        cr = r["classification_report"]
        print(f"{method:<10} {r['accuracy']:>10.3f} {cr['macro avg']['f1-score']:>10.3f} "
              f"{cr['positive']['f1-score']:>10.3f} {cr['neutral']['f1-score']:>10.3f} "
              f"{cr['negative']['f1-score']:>10.3f}")

    print("\n" + "=" * 49)
    print("Inter-Method Agreement (Full Dataset)")
    print("=" * 49)
    kappa_header = "Cohen's κ"
    print(f"{'Pair':<25} {'Agreement%':>12} {kappa_header:>10}")
    print("-" * 49)
    for key, r in results["agreement"].items():
        display = key.replace("_vs_", " vs ")
        print(f"{display:<25} {r['agreement_pct']:>11.1f}% {r['cohens_kappa']:>10.3f}")
    print()
