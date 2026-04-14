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
    # Implementation:
    # 1. accuracy = accuracy_score(true_labels, predicted_labels)
    # 2. report = classification_report(true_labels, predicted_labels,
    #                labels=LABEL_ORDER, output_dict=True, zero_division=0)
    # 3. cm = confusion_matrix(true_labels, predicted_labels, labels=LABEL_ORDER)
    # 4. Return dict
    raise NotImplementedError("Implement in Phase 2, Day 5")


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
    # Implementation:
    # 1. agreement = sum(a == b for a, b in zip(labels_a, labels_b)) / len(labels_a) * 100
    # 2. kappa = cohen_kappa_score(labels_a, labels_b)
    # 3. Return dict
    raise NotImplementedError("Implement in Phase 2, Day 5")


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
    # Implementation:
    # 1. Filter to test split: test_df = df[df["split"] == "test"]
    # 2. For each method in METHODS:
    #      evaluate_classifier(test_df["true_label"], test_df[f"{method}_label"], method)
    # 3. For each pair (i, j) where i < j in METHODS:
    #      evaluate_agreement(df[f"{i}_label"], df[f"{j}_label"], i, j)
    #      NOTE: Agreement computed on FULL dataset, not just test
    # 4. Print formatted tables
    # 5. Return nested dict
    raise NotImplementedError("Implement in Phase 2, Day 5")


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
    raise NotImplementedError("Implement in Phase 2, Day 5")
