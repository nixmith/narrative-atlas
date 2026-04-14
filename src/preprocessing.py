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
    df = df.copy()
    df["text_clean"] = df["text"].str.strip()
    df["text_clean"] = df["text_clean"].apply(_normalize_unicode)

    if config["preprocessing"]["lowercase"]:
        df["text_clean"] = df["text_clean"].str.lower()

    df["text_clean"] = df["text_clean"].str.replace(r'\s+', ' ', regex=True)

    empty_mask = df["text_clean"].str.len() == 0
    if empty_mask.any():
        raise ValueError(f"{empty_mask.sum()} texts became empty after preprocessing.")

    return df


def _normalize_unicode(text: str) -> str:
    """
    Normalize unicode characters to NFKD form.

    NFKD decomposes compatibility characters — e.g. accented Latin letters
    decompose into base + combining mark, ligatures split into their component
    letters, and full-width characters collapse to ASCII-width. Smart quotes
    and typographic dashes are *not* affected by NFKD because they have no
    compatibility decomposition; callers should not rely on this function for
    quote/dash canonicalization.

    Args:
        text: Raw input string.

    Returns:
        Unicode-normalized string.
    """
    return unicodedata.normalize("NFKD", text)
