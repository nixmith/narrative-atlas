"""
Text preprocessing for Narrative Atlas.

Minimal, deliberate preprocessing for financial headlines.
Does NOT aggressively transform text — financial text needs its
punctuation (VADER uses it) and numbers (financial figures matter).

Usage:
    from src.preprocessing import preprocess
    df = preprocess(headlines_df, config)
    # df now has 'text_clean' column
"""

import unicodedata
import re

import pandas as pd


def preprocess(df: pd.DataFrame, config: dict) -> pd.DataFrame:
    """
    Clean and normalize headline text. Adds 'text_clean' column.

    Steps applied (in order):
      1. Strip leading/trailing whitespace
      2. Normalize unicode to NFKD form (handles smart quotes, etc.)
      3. Optionally lowercase (config['preprocessing']['lowercase'])
      4. Collapse multiple whitespace characters to single space
      5. Validate: no empty strings after cleaning

    Args:
        df: DataFrame with 'text' column.
        config: Loaded config dict.

    Returns:
        Same DataFrame with 'text_clean' column added.

    Raises:
        ValueError: If any text becomes empty after preprocessing.
    """
    # Implementation steps:
    # 1. df["text_clean"] = df["text"].str.strip()
    # 2. Apply _normalize_unicode to each value
    # 3. If config["preprocessing"]["lowercase"]: lowercase it
    # 4. Collapse whitespace: re.sub(r'\s+', ' ', text)
    # 5. Check for empty strings, raise if any found
    raise NotImplementedError("Implement in Phase 1, Day 1")


def _normalize_unicode(text: str) -> str:
    """
    Normalize unicode characters to NFKD form.

    Converts smart quotes to straight quotes, normalizes dashes,
    and handles other unicode variations common in financial news.

    Args:
        text: Raw input string.

    Returns:
        Unicode-normalized string.
    """
    return unicodedata.normalize("NFKD", text)
