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
    # Implementation steps:
    # 1. Check if cached CSV exists at config path
    # 2. If not, load from HuggingFace datasets library:
    #      from datasets import load_dataset
    #      ds = load_dataset("financial_phrasebank", config["data"]["fpb_config"])
    #    The dataset has 'sentence' and 'label' columns.
    #    Label mapping: {0: 'negative', 1: 'neutral', 2: 'positive'}
    # 3. Convert to pandas DataFrame, rename columns to 'text' and 'true_label'
    # 4. Stratified train/test split using config test_size and random seed
    # 5. Add 'split' column
    # 6. Save to CSV cache
    # 7. Validate: no nulls, no empty strings, labels in expected set
    # 8. Print summary: total count, label distribution, split sizes
    raise NotImplementedError("Implement in Phase 1, Day 1")


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
    # Implementation steps:
    # 1. Check if cached CSV exists
    # 2. If not, download:
    #      import yfinance as yf
    #      ticker = yf.Ticker(config["data"]["ticker"])
    #      hist = ticker.history(start=config["data"]["price_start"],
    #                            end=config["data"]["price_end"])
    # 3. Keep only 'Close' column, rename to 'close'
    # 4. Reset index to get 'Date' as column, rename to 'date'
    # 5. Save to CSV cache
    # 6. Validate: no nulls, dates are monotonically increasing
    # 7. Print summary: date range, row count
    raise NotImplementedError("Implement in Phase 1, Day 1")


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
    raise NotImplementedError("Implement in Phase 1, Day 1")


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
    raise NotImplementedError("Implement in Phase 1, Day 1")
