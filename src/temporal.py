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
    import numpy as np
    from src.config import get_seed

    seed = get_seed(config)
    start = pd.to_datetime(config["data"]["price_start"])
    end = pd.to_datetime(config["data"]["price_end"])

    bdays = pd.bdate_range(start, end)

    rng = np.random.RandomState(seed)
    shuffled_idx = rng.permutation(len(df))

    dates = [bdays[i % len(bdays)] for i in range(len(df))]

    df = df.copy()
    df = df.iloc[shuffled_idx].reset_index(drop=True)
    df["date"] = dates[:len(df)]
    df = df.sort_values("date").reset_index(drop=True)

    return df


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
    df["date"] = pd.to_datetime(df["date"])
    prices_df = prices_df.copy()
    prices_df["date"] = pd.to_datetime(prices_df["date"])

    df["week_start"] = df["date"].dt.to_period("W-MON").dt.start_time
    weekly_sent = df.groupby("week_start").agg(
        volume=("date", "count"),
        vader_mean=("vader_score", "mean"),
        logreg_mean=("logreg_score", "mean"),
        finbert_mean=("finbert_score", "mean"),
        finbert_std=("finbert_score", "std"),
    ).reset_index()

    prices_df["week_start"] = prices_df["date"].dt.to_period("W-MON").dt.start_time
    weekly_price = prices_df.groupby("week_start").agg(
        open_price=("close", "first"),
        close_price=("close", "last"),
    ).reset_index()
    weekly_price["weekly_return"] = (
        (weekly_price["close_price"] - weekly_price["open_price"])
        / weekly_price["open_price"]
    )

    weekly = pd.merge(
        weekly_sent,
        weekly_price[["week_start", "weekly_return"]],
        on="week_start",
        how="inner",
    )

    weekly["next_return"] = weekly["weekly_return"].shift(-1)
    weekly = weekly.dropna(subset=["next_return"])

    from src.config import get_path, load_config
    config = load_config()
    path = get_path(config, "weekly_aggregated")
    weekly.to_csv(path, index=False)
    print(f"  Saved weekly aggregation: {len(weekly)} weeks to {path}")

    return weekly


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
    results = {}
    print("\n" + "=" * 55)
    print("Sentiment-Return Correlations")
    print("=" * 55)
    header_pearson = "Pearson r"
    header_spearman = "Spearman rho"
    print(f"{'Method':<10} {header_pearson:>10} {'p-value':>10} {header_spearman:>14} {'p-value':>10}")
    print("-" * 55)

    for method in METHODS:
        col = f"{method}_mean"
        x = weekly_df[col].dropna()
        y = weekly_df.loc[x.index, "next_return"].dropna()
        common = x.index.intersection(y.index)
        x, y = x.loc[common], y.loc[common]

        pr, pp = stats.pearsonr(x, y)
        sr, sp = stats.spearmanr(x, y)

        results[method] = {
            "pearson_r": pr,
            "pearson_p": pp,
            "spearman_rho": sr,
            "spearman_p": sp,
        }
        print(f"{method:<10} {pr:>10.4f} {pp:>10.4f} {sr:>14.4f} {sp:>10.4f}")

    return results
