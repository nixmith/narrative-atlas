"""
Narrative Atlas — Pipeline Orchestrator

Entry point that runs the full pipeline end-to-end:
  1. Load data
  2. Preprocess
  3. Score with all three methods
  4. Merge and export master CSV
  5. Evaluate
  6. Temporal analysis
  7. Generate figures

Usage:
    python run_pipeline.py             # Run full pipeline
    python run_pipeline.py --skip-figures  # Skip visualization (faster for dev)
"""

import argparse
import time
import sys

import pandas as pd

from src.config import load_config, get_path, get_seed
from src.data_loader import load_headlines, load_prices
from src.preprocessing import preprocess
from src.scorers import VaderScorer, LogRegScorer, FinBERTScorer
from src.evaluation import evaluate_all, print_summary
from src.temporal import assign_dates, aggregate_weekly, compute_correlations
from src.visualizations import generate_all_figures


def run_pipeline(skip_figures: bool = False) -> None:
    """
    Execute the full Narrative Atlas pipeline.

    Steps:
      1. Load config
      2. Set random seeds (numpy, torch if available)
      3. Load headlines and prices
      4. Preprocess headlines
      5. Score with VADER (no training needed)
      6. Train + Score with LogReg
      7. Score with FinBERT
      8. Save master scored CSV
      9. Run evaluation, print results
     10. Run temporal analysis (assign dates, aggregate, correlate)
     11. Generate all figures (unless --skip-figures)
     12. Print total runtime
    """
    t_start = time.time()
    print("=" * 60)
    print("NARRATIVE ATLAS — Full Pipeline")
    print("=" * 60)

    # ── Stage 1: Configuration ─────────────────────────────
    print("\n[1/7] Loading configuration...")
    config = load_config()
    seed = get_seed(config)

    import numpy as np
    np.random.seed(seed)

    try:
        import torch
        torch.manual_seed(seed)
    except ImportError:
        pass

    # ── Stage 2: Data Loading ──────────────────────────────
    print("\n[2/7] Loading data...")
    headlines_df = load_headlines(config)
    prices_df = load_prices(config)
    print(f"  Headlines: {len(headlines_df)} rows")
    print(f"  Prices: {len(prices_df)} trading days")

    # ── Stage 3: Preprocessing ─────────────────────────────
    print("\n[3/7] Preprocessing text...")
    headlines_df = preprocess(headlines_df, config)
    print(f"  Added 'text_clean' column")

    # ── Stage 4: Scoring ───────────────────────────────────
    print("\n[4/7] Scoring headlines...")

    # VADER
    print("  VADER...")
    vader = VaderScorer(config)
    headlines_df = vader.score_dataframe(headlines_df)
    print(f"    Done. Sample score: {headlines_df['vader_score'].iloc[0]:.3f}")

    # LogReg (train first if needed)
    print("  Logistic Regression...")
    logreg = LogRegScorer(config)
    if not logreg.is_trained():
        train_df = headlines_df[headlines_df["split"] == "train"]
        print("    Training on train split...")
        logreg.train(
            train_df["text_clean"].tolist(),
            train_df["true_label"].tolist(),
        )
    headlines_df = logreg.score_dataframe(headlines_df)
    print(f"    Done. Sample score: {headlines_df['logreg_score'].iloc[0]:.3f}")

    # FinBERT
    print("  FinBERT...")
    finbert = FinBERTScorer(config)
    headlines_df = finbert.score_dataframe(headlines_df)
    print(f"    Done. Sample score: {headlines_df['finbert_score'].iloc[0]:.3f}")

    # ── Stage 5: Export Master CSV ─────────────────────────
    print("\n[5/7] Saving scored headlines...")
    output_path = get_path(config, "scored_headlines")
    headlines_df.to_csv(output_path, index=False)
    print(f"  Saved: {output_path} ({len(headlines_df)} rows)")

    # ── Stage 6: Evaluation ────────────────────────────────
    print("\n[6/7] Evaluating...")
    results = evaluate_all(headlines_df, config)
    print_summary(results)

    # ── Stage 7: Temporal Analysis + Figures ───────────────
    print("\n[7/7] Temporal analysis...")
    headlines_df = assign_dates(headlines_df, config)
    weekly_df = aggregate_weekly(headlines_df, prices_df)
    corr_results = compute_correlations(weekly_df, config)

    if not skip_figures:
        print("\nGenerating figures...")
        generate_all_figures(config)
    else:
        print("\nSkipping figures (--skip-figures)")

    # ── Done ───────────────────────────────────────────────
    elapsed = time.time() - t_start
    print(f"\n{'=' * 60}")
    print(f"Pipeline complete in {elapsed:.1f}s")
    print(f"{'=' * 60}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Narrative Atlas Pipeline")
    parser.add_argument(
        "--skip-figures",
        action="store_true",
        help="Skip figure generation (faster for development)",
    )
    args = parser.parse_args()
    run_pipeline(skip_figures=args.skip_figures)
