"""
Abstract base class for all Narrative Atlas sentiment scorers.

Defines the contract that every scorer must satisfy:
  - Accept config at init
  - Implement score_batch() returning standardized columns
  - Use the normalizer for consistent score/label output

The base class provides score_dataframe() for free — subclasses
only implement score_batch().

Design rationale:
  This interface exists so the pipeline, evaluation, and visualization
  code never need to know which scorer produced the data. They operate
  on '{method}_score' and '{method}_label' columns. When Narrative Atlas
  adds new scorers (aspect-based, embedding drift, framing classifiers),
  they plug in by implementing this same interface.
"""

from abc import ABC, abstractmethod

import pandas as pd

from src.normalizer import score_to_label


class BaseScorer(ABC):
    """
    Abstract base class for sentiment scorers.

    Subclasses must implement:
        name (property) — short identifier ('vader', 'logreg', 'finbert')
        score_batch(texts) — score a list of strings, return DataFrame

    The base class provides:
        score_dataframe(df) — convenience method that calls score_batch()
                              and merges results into the input DataFrame
    """

    def __init__(self, config: dict):
        """
        Args:
            config: Full config dict (scorer reads its own section).
        """
        self.config = config

    @property
    @abstractmethod
    def name(self) -> str:
        """
        Short identifier for this scorer.

        Used as prefix for output column names: '{name}_score', '{name}_label'.
        Must be lowercase, alphanumeric, no spaces.
        Examples: 'vader', 'logreg', 'finbert'
        """
        ...

    @abstractmethod
    def score_batch(self, texts: list[str]) -> pd.DataFrame:
        """
        Score a list of texts.

        Args:
            texts: List of preprocessed headline strings. Never empty.

        Returns:
            DataFrame with exactly len(texts) rows and two columns:
                '{self.name}_score': float in [-1.0, +1.0]
                '{self.name}_label': str in {'positive', 'neutral', 'negative'}

            Row i of the output corresponds to texts[i].

        Raises:
            ValueError: If texts is empty.
        """
        ...

    def score_dataframe(self, df: pd.DataFrame, text_col: str = "text_clean") -> pd.DataFrame:
        """
        Score all rows in a DataFrame. Adds score and label columns.

        This method is provided by the base class. Subclasses do NOT override.

        Args:
            df: DataFrame with a text column to score.
            text_col: Name of the column containing preprocessed text.

        Returns:
            Same DataFrame with '{name}_score' and '{name}_label' columns added.

        Raises:
            KeyError: If text_col not found in df.
            ValueError: If any texts are null or empty.
        """
        if text_col not in df.columns:
            raise KeyError(f"Column '{text_col}' not found in DataFrame. Available: {list(df.columns)}")

        texts = df[text_col].tolist()

        if not texts:
            raise ValueError("Cannot score an empty DataFrame.")

        results = self.score_batch(texts)

        score_col = f"{self.name}_score"
        label_col = f"{self.name}_label"

        df[score_col] = results[score_col].values
        df[label_col] = results[label_col].values

        return df
