"""
Visualization generators for Narrative Atlas.

Produces five publication-quality figures:
  1. Sentiment timeline with price overlay
  2. Sentiment distributions by method
  3. Method agreement heatmap
  4. Keyword frequency spectrogram
  5. Volume-sentiment scatter

All figures use consistent colors from config.yaml.
All figures save at 300 DPI to the configured output directory.

Usage:
    from src.visualizations import generate_all_figures
    generate_all_figures(config)
"""

from pathlib import Path

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import seaborn as sns
from sklearn.feature_extraction.text import TfidfVectorizer

from src.config import get_path


METHODS = ["vader", "logreg", "finbert"]
METHOD_DISPLAY = {"vader": "VADER", "logreg": "LogReg", "finbert": "FinBERT"}


def setup_style(config: dict) -> None:
    """
    Set matplotlib rcParams for consistent figure styling.

    Sets:
      - Font: serif family, 11pt default
      - Axes: light gray grid, white background
      - Figure: tight layout by default
      - Savefig: white facecolor, 300 DPI
    """
    plt.rcParams.update({
        "font.family": "serif",
        "font.size": 11,
        "axes.grid": True,
        "axes.grid.which": "major",
        "grid.alpha": 0.3,
        "grid.linewidth": 0.5,
        "axes.facecolor": "white",
        "figure.facecolor": "white",
        "figure.dpi": 100,
        "savefig.dpi": config["visualization"]["dpi"],
        "savefig.facecolor": "white",
        "savefig.bbox": "tight",
    })


def _get_colors(config: dict) -> dict:
    """Get method colors from config."""
    return config["visualization"]["colors"]


def _save_figure(fig: plt.Figure, filename: str, config: dict) -> None:
    """Save figure to configured output directory."""
    output_dir = Path(config["visualization"]["output_dir"])
    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / filename
    fig.savefig(path, dpi=config["visualization"]["dpi"], bbox_inches="tight")
    plt.close(fig)
    print(f"  Saved: {path}")


# ─────────────────────────────────────────────────────────────
# Figure 1: Sentiment Timeline with Price Overlay
# ─────────────────────────────────────────────────────────────

def fig1_sentiment_timeline(
    df: pd.DataFrame,
    prices_df: pd.DataFrame,
    config: dict,
) -> None:
    """
    Dual-axis time series: sentiment traces + stock price.

    Left y-axis: rolling 7-day mean sentiment for each method (3 colored lines)
    Right y-axis: daily close price (semi-transparent gray area fill)
    X-axis: date

    Annotations: 2-3 vertical dashed lines marking known events
    (e.g., earnings dates, WWDC, product launches).

    Implementation:
      1. Group df by date, compute daily mean per method
      2. Apply rolling mean (window from config)
      3. Create figure with config figsize_timeline
      4. Plot three sentiment lines on left axis
      5. Plot price area fill on right axis (twinx)
      6. Add event annotations as axvline + text
      7. Add legend, axis labels
      8. Save via _save_figure

    Args:
        df: Scored DataFrame with 'date' column.
        prices_df: Price DataFrame with 'date' and 'close'.
        config: Loaded config dict.
    """
    colors = _get_colors(config)
    window = config["visualization"]["rolling_window"]
    figsize = config["visualization"]["figsize_timeline"]

    df = df.copy()
    df["date"] = pd.to_datetime(df["date"])
    daily = df.groupby("date").agg(
        vader=("vader_score", "mean"),
        logreg=("logreg_score", "mean"),
        finbert=("finbert_score", "mean"),
    ).sort_index()

    fig, ax1 = plt.subplots(figsize=figsize)

    for method in METHODS:
        rolled = daily[method].rolling(window, min_periods=1).mean()
        ax1.plot(
            daily.index, rolled,
            color=colors[method], linewidth=1.5,
            label=METHOD_DISPLAY[method], alpha=0.85,
        )

    ax1.set_ylabel("Sentiment Score (rolling mean)")
    ax1.set_ylim(-0.6, 0.8)
    ax1.axhline(0, color="gray", linewidth=0.5, linestyle="--", alpha=0.5)

    ax2 = ax1.twinx()
    prices_plot = prices_df.copy()
    prices_plot["date"] = pd.to_datetime(prices_plot["date"])
    prices_plot = prices_plot.set_index("date")
    price_range = prices_plot.loc[daily.index.min():daily.index.max()]
    ax2.fill_between(
        price_range.index, price_range["close"],
        alpha=0.1, color=colors["price"],
    )
    ax2.plot(
        price_range.index, price_range["close"],
        color=colors["price"], linewidth=0.8, alpha=0.3,
    )
    ax2.set_ylabel(f"{config['data']['ticker']} Close ($)")

    ax1.legend(loc="upper left", fontsize=9)
    ax1.set_xlabel("Date")
    ax1.xaxis.set_major_formatter(mdates.DateFormatter("%b %Y"))
    fig.autofmt_xdate()

    _save_figure(fig, "fig1_sentiment_timeline.png", config)


# ─────────────────────────────────────────────────────────────
# Figure 2: Sentiment Distributions by Method
# ─────────────────────────────────────────────────────────────

def fig2_sentiment_distributions(df: pd.DataFrame, config: dict) -> None:
    """
    Three violin plots showing score distribution per method.

    One violin per method, all on the same axes for comparison.
    Mark mean and median on each violin.

    Implementation:
      1. Reshape data: melt score columns into long format
         (columns: method, score)
      2. Create figure with config figsize_distributions
      3. seaborn.violinplot(x='method', y='score', data=melted,
                            palette=colors, inner='quartile')
      4. Add horizontal line at y=0 (neutral reference)
      5. Axis labels: "Method" / "Sentiment Score"
      6. Save

    Args:
        df: Scored DataFrame.
        config: Loaded config dict.
    """
    colors = _get_colors(config)
    figsize = config["visualization"]["figsize_distributions"]

    score_data = []
    for method in METHODS:
        scores = df[f"{method}_score"].values
        for s in scores:
            score_data.append({"method": METHOD_DISPLAY[method], "score": s})
    melted = pd.DataFrame(score_data)

    palette = {METHOD_DISPLAY[m]: colors[m] for m in METHODS}

    fig, ax = plt.subplots(figsize=figsize)
    sns.violinplot(
        x="method", y="score", data=melted,
        palette=palette, inner="quartile", ax=ax, cut=0,
    )
    ax.axhline(0, color="gray", linewidth=0.5, linestyle="--", alpha=0.5)
    ax.set_xlabel("Method")
    ax.set_ylabel("Sentiment Score")
    ax.set_title("Score Distribution by Method")

    _save_figure(fig, "fig2_sentiment_distributions.png", config)


# ─────────────────────────────────────────────────────────────
# Figure 3: Method Agreement Heatmap
# ─────────────────────────────────────────────────────────────

def fig3_method_agreement(df: pd.DataFrame, config: dict) -> None:
    """
    3×3 heatmap of pairwise label agreement between methods.

    Cell (i, j) = percentage of headlines where method i and method j
    assign the same label. Diagonal = 100%.
    Annotated with both agreement % and Cohen's κ.

    Implementation:
      1. Compute agreement % and κ for each pair (including self-pairs = 100%, κ=1.0)
      2. Build 3×3 numpy array
      3. Create figure with config figsize_agreement
      4. seaborn.heatmap with annot=True, fmt strings showing both % and κ
      5. Label axes with method display names
      6. Save

    Args:
        df: Scored DataFrame.
        config: Loaded config dict.
    """
    raise NotImplementedError("Implement in Phase 2, Day 9")


# ─────────────────────────────────────────────────────────────
# Figure 4: Keyword Frequency Spectrogram
# ─────────────────────────────────────────────────────────────

def fig4_keyword_spectrogram(df: pd.DataFrame, config: dict) -> None:
    """
    Heatmap of top TF-IDF keywords × time periods.

    Rows: top 12-15 keywords by mean TF-IDF weight across corpus
    Columns: time periods (monthly or biweekly)
    Cell color: row-normalized frequency (0-1 per keyword)

    Implementation:
      1. Fit TfidfVectorizer on all text_clean
      2. Get feature names and mean TF-IDF weight per term
      3. Select top 12-15 terms (excluding stopwords if needed)
      4. For each time period, compute frequency of each selected term
      5. Row-normalize: each row's values scaled to [0, 1]
      6. Plot as seaborn.heatmap with clean labels
      7. Save

    Args:
        df: Scored DataFrame with 'date' and 'text_clean' columns.
        config: Loaded config dict.
    """
    raise NotImplementedError("Implement in Phase 3, Day 10")


# ─────────────────────────────────────────────────────────────
# Figure 5: Volume-Sentiment Scatter
# ─────────────────────────────────────────────────────────────

def fig5_volume_sentiment_scatter(
    weekly_df: pd.DataFrame,
    config: dict,
) -> None:
    """
    Scatter plot: weekly volume vs. mean sentiment, colored by outcome.

    Each point = one week.
    X-axis: article count (volume)
    Y-axis: mean FinBERT sentiment score
    Color: green if next-week return > 0, red if < 0
    Optional: point size = finbert_std (larger = more disagreement)

    Implementation:
      1. Separate weekly_df into up/down based on next_return
      2. Create figure with config figsize_scatter
      3. Plot up weeks as green scatter, down weeks as red scatter
      4. Add axis labels, legend ("Next week: ↑" / "Next week: ↓")
      5. Save

    Args:
        weekly_df: Weekly aggregated DataFrame from temporal.py.
        config: Loaded config dict.
    """
    raise NotImplementedError("Implement in Phase 3, Day 11")


# ─────────────────────────────────────────────────────────────
# Master generator
# ─────────────────────────────────────────────────────────────

def generate_all_figures(config: dict) -> None:
    """
    Load processed data and generate all five figures.

    Called by run_pipeline.py as the final pipeline stage.

    Implementation:
      1. setup_style(config)
      2. Load headlines_scored.csv and weekly_aggregated.csv
      3. Load prices data
      4. Call each fig*() function
      5. Print summary of generated figures
    """
    raise NotImplementedError("Implement in Phases 2-3")
