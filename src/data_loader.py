"""
Data loading for Narrative Atlas.

Downloads (if needed) and loads:
  1. FinancialPhraseBank — financial news sentences with expert sentiment labels
  2. AAPL stock price data — daily close prices for temporal analysis

All raw data is saved to data/raw/ and never modified.
Train/test splits are deterministic (seeded stratified split).

Usage:
    from src.config import load_config
    from src.data_loader import load_headlines, load_prices

    config = load_config()
    headlines_df = load_headlines(config)
    prices_df = load_prices(config)
"""

import pandas as pd
import numpy as np
from pathlib import Path
from sklearn.model_selection import train_test_split

from src.config import get_path, get_seed


def load_headlines(config: dict) -> pd.DataFrame:
    """
    Load FinancialPhraseBank data with deterministic train/test split.

    On first call, downloads from HuggingFace and caches to data/raw/.
    On subsequent calls, loads from cache.

    Args:
        config: Loaded config dict.

    Returns:
        DataFrame with columns:
            text: str        — raw headline text
            true_label: str  — 'positive', 'neutral', or 'negative'
            split: str       — 'train' or 'test'

    Raises:
        ValueError: If loaded data has unexpected labels or empty texts.
    """
    cache_path = get_path(config, "raw_headlines")

    if cache_path.exists():
        df = pd.read_csv(cache_path)
        print(f"  Loaded cached headlines: {len(df)} rows")
    else:
        from datasets import load_dataset
        ds = load_dataset("financial_phrasebank", config["data"]["fpb_config"],
                          trust_remote_code=True)
        df = pd.DataFrame(ds["train"])

        label_map = {0: "negative", 1: "neutral", 2: "positive"}
        df["true_label"] = df["label"].map(label_map)
        df = df.rename(columns={"sentence": "text"})
        df = df[["text", "true_label"]]

        train_df, test_df = train_test_split(
            df,
            test_size=config["data"]["test_size"],
            stratify=df["true_label"],
            random_state=get_seed(config),
        )
        train_df = train_df.copy()
        test_df = test_df.copy()
        train_df["split"] = "train"
        test_df["split"] = "test"
        df = pd.concat([train_df, test_df], ignore_index=True)

        cache_path.parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(cache_path, index=False)
        print(f"  Downloaded and cached: {len(df)} rows")

    _validate_headlines(df)

    print(f"  Label distribution:")
    for label in ["positive", "neutral", "negative"]:
        count = (df["true_label"] == label).sum()
        print(f"    {label}: {count} ({count / len(df) * 100:.1f}%)")

    return df


def load_prices(config: dict) -> pd.DataFrame:
    """
    Load stock price data from Yahoo Finance.

    On first call, downloads via yfinance and caches to data/raw/.
    On subsequent calls, loads from cache.

    Args:
        config: Loaded config dict.

    Returns:
        DataFrame with columns:
            date: datetime  — trading date (also set as index)
            close: float    — adjusted close price

    Raises:
        ValueError: If no price data returned for the configured ticker/range.
    """
    cache_path = get_path(config, "raw_prices")

    if cache_path.exists():
        df = pd.read_csv(cache_path, parse_dates=["date"])
        print(f"  Loaded cached prices: {len(df)} rows")
    else:
        import yfinance as yf
        ticker = yf.Ticker(config["data"]["ticker"])
        hist = ticker.history(
            start=config["data"]["price_start"],
            end=config["data"]["price_end"],
        )
        if hist.empty:
            raise ValueError(
                f"No price data returned for {config['data']['ticker']} "
                f"({config['data']['price_start']} to {config['data']['price_end']})"
            )
        df = hist[["Close"]].reset_index()
        df.columns = ["date", "close"]
        df["date"] = pd.to_datetime(df["date"]).dt.tz_localize(None)

        cache_path.parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(cache_path, index=False)
        print(f"  Downloaded and cached: {len(df)} rows")

    _validate_prices(df)
    print(f"  Prices: {len(df)} days, {df['date'].min().date()} to {df['date'].max().date()}")
    return df


def _validate_headlines(df: pd.DataFrame) -> None:
    """
    Validate headlines DataFrame meets contract.

    Checks:
      - No null values in any column
      - No empty strings in 'text'
      - 'true_label' values are exactly {'positive', 'neutral', 'negative'}
      - 'split' values are exactly {'train', 'test'}
      - At least 100 rows in each split

    Raises:
        ValueError: With descriptive message if any check fails.
    """
    required = {"text", "true_label", "split"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(
            f"Headlines DataFrame missing required columns: {missing}. "
            f"Cache file may be corrupted — delete data/raw/financial_phrasebank.csv and re-run."
        )
    if df.isnull().any().any():
        raise ValueError(f"Null values found in headlines DataFrame")
    if (df["text"].str.len() == 0).any():
        raise ValueError("Empty strings found in 'text' column")
    expected_labels = {"positive", "neutral", "negative"}
    actual_labels = set(df["true_label"].unique())
    if actual_labels != expected_labels:
        raise ValueError(f"Unexpected labels: {actual_labels}, expected {expected_labels}")
    expected_splits = {"train", "test"}
    actual_splits = set(df["split"].unique())
    if actual_splits != expected_splits:
        raise ValueError(f"Unexpected splits: {actual_splits}, expected {expected_splits}")
    for split in ["train", "test"]:
        count = (df["split"] == split).sum()
        if count < 100:
            raise ValueError(f"Only {count} rows in '{split}' split, expected at least 100")


def _validate_prices(df: pd.DataFrame) -> None:
    """
    Validate prices DataFrame meets contract.

    Checks:
      - No null values
      - 'close' values are all positive
      - At least 200 trading days of data

    Raises:
        ValueError: With descriptive message if any check fails.
    """
    required = {"date", "close"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(
            f"Prices DataFrame missing required columns: {missing}. "
            f"Cache file may be corrupted — delete data/raw/aapl_prices.csv and re-run."
        )
    if df.isnull().any().any():
        raise ValueError("Null values found in prices DataFrame")
    if (df["close"] <= 0).any():
        raise ValueError("Non-positive close prices found")
    if len(df) < 200:
        raise ValueError(f"Only {len(df)} trading days, expected at least 200")
