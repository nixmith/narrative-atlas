"""
Temporal analysis for Narrative Atlas.

Handles:
  1. Assigning dates to headlines (pseudo-temporal for proof-of-concept)
  2. Weekly aggregation of sentiment scores and article volume
  3. Alignment with stock returns
  4. Sentiment-return correlation analysis

Usage:
    from src.temporal import assign_dates, aggregate_weekly, compute_correlations
    df = assign_dates(scored_df, config)
    weekly_df = aggregate_weekly(df, prices_df)
    corr = compute_correlations(weekly_df, config)
"""

import pandas as pd
import numpy as np
from scipy import stats

from src.config import get_path


METHODS = ["vader", "logreg", "finbert"]


def assign_dates(df: pd.DataFrame, config: dict) -> pd.DataFrame:
    """
    Assign pseudo-dates to headlines for temporal analysis.

    Strategy: Distribute headlines evenly across the price data date range.
    Headlines are shuffled (seeded) first, then assigned dates at regular
    intervals. This is a proof-of-concept simplification — real Narrative
    Atlas would use actual publication timestamps.

    Args:
        df: Scored DataFrame (all headlines).
        config: Loaded config dict.

    Returns:
        Same DataFrame with 'date' column (datetime) added.

    Note:
        This is explicitly documented as a simplification. The temporal
        patterns observed are artifacts of the distribution method, not
        real temporal signals. The value is in demonstrating the
        visualization and analysis infrastructure.
    """
    # Implementation:
    # 1. Create date range from config price_start to price_end (business days only)
    # 2. Shuffle df with seed for reproducibility
    # 3. Assign dates by cycling through the date range
    #    (multiple headlines can share a date)
    # 4. Sort by date
    raise NotImplementedError("Implement in Phase 2, Day 6")


def aggregate_weekly(df: pd.DataFrame, prices_df: pd.DataFrame) -> pd.DataFrame:
    """
    Aggregate sentiment and volume by week, aligned with stock returns.

    Args:
        df: Scored DataFrame with 'date' column.
        prices_df: Price DataFrame with 'date' and 'close' columns.

    Returns:
        DataFrame with columns:
            week_start: datetime (Monday of each week)
            volume: int (headline count)
            vader_mean: float
            logreg_mean: float
            finbert_mean: float
            finbert_std: float (for scatter plot point sizing)
            weekly_return: float (% return for that week)
            next_return: float (% return for the NEXT week, shifted)

        Saved to data/processed/weekly_aggregated.csv
    """
    # Implementation:
    # 1. headlines: group by pd.Grouper(key='date', freq='W-MON')
    # 2. Compute mean score per method, count, std for finbert
    # 3. prices: resample to weekly, compute weekly return =
    #    (last_close - first_close) / first_close
    # 4. Merge on week_start
    # 5. next_return = weekly_return.shift(-1) — this is the NEXT week's return
    # 6. Drop rows with NaN next_return (last week has no future)
    # 7. Save to CSV
    raise NotImplementedError("Implement in Phase 2, Day 6")


def compute_correlations(weekly_df: pd.DataFrame, config: dict) -> dict:
    """
    Compute sentiment-return correlations.

    For each method, compute:
      - Pearson r and p-value: linear correlation
      - Spearman ρ and p-value: rank correlation (robust to outliers)

    Both correlate that method's weekly mean sentiment with NEXT-week return.

    Args:
        weekly_df: Weekly aggregated DataFrame.
        config: Loaded config dict.

    Returns:
        Dict of {method: {pearson_r, pearson_p, spearman_rho, spearman_p}}

    Also prints formatted correlation table.
    """
    # Implementation:
    # For each method in METHODS:
    #   x = weekly_df[f"{method}_mean"]
    #   y = weekly_df["next_return"]
    #   Drop any NaN pairs
    #   pearson_r, pearson_p = stats.pearsonr(x, y)
    #   spearman_rho, spearman_p = stats.spearmanr(x, y)
    raise NotImplementedError("Implement in Phase 2, Day 6")
