"""
Logistic Regression + TF-IDF sentiment scorer for Narrative Atlas.

A classical supervised classifier using TF-IDF feature extraction
and logistic regression. Domain-adapted through training on
FinancialPhraseBank.

Course connection:
  - Chapter 4 §4.3: Logistic regression for sentiment classification
  - Chapter 5: TF-IDF weighting for document/term representation

Properties:
  - Requires training on labeled data (FPB train split)
  - Uses scikit-learn Pipeline for reproducibility
  - Score: P(positive) - P(negative) from predict_proba()
  - Interpretable: top features can be inspected via TF-IDF weights
"""

from pathlib import Path

import pandas as pd
import numpy as np
import joblib
from sklearn.pipeline import Pipeline
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression

from src.scorers.base import BaseScorer
from src.normalizer import normalize_score, score_to_label
from src.config import get_seed


class LogRegScorer(BaseScorer):
    """
    TF-IDF + Logistic Regression sentiment scorer.

    Supports two modes:
      train() — fit on labeled data and save the pipeline to disk
      score_batch() — load saved pipeline and predict

    The pipeline is a scikit-learn Pipeline object:
      TfidfVectorizer(max_features, ngram_range) → LogisticRegression(...)
    """

    def __init__(self, config: dict):
        super().__init__(config)
        self._scorer_config = config["scorers"]["logreg"]
        self._model_path = Path(self._scorer_config["model_path"])
        self._pipeline = None

    @property
    def name(self) -> str:
        return "logreg"

    def train(self, texts: list[str], labels: list[str]) -> None:
        """
        Fit the TF-IDF + LogReg pipeline on training data and save to disk.

        Implementation:
          1. Build Pipeline:
               TfidfVectorizer(
                   max_features=config max_features,
                   ngram_range=tuple(config ngram_range)
               )
               LogisticRegression(
                   max_iter=config max_iter,
                   class_weight=config class_weight,
                   random_state=seed
               )
          2. pipeline.fit(texts, labels)
          3. Save with joblib.dump() to self._model_path
          4. Print training accuracy
          5. Store pipeline in self._pipeline for immediate use

        Args:
            texts: List of preprocessed training texts.
            labels: List of true labels ('positive', 'neutral', 'negative').

        Raises:
            ValueError: If texts and labels have different lengths.
        """
        raise NotImplementedError("Implement in Phase 1, Day 3")

    def is_trained(self) -> bool:
        """Check if a saved model file exists on disk."""
        return self._model_path.exists()

    def _load_pipeline(self) -> None:
        """Load the saved pipeline from disk if not already in memory."""
        if self._pipeline is None:
            if not self.is_trained():
                raise RuntimeError(
                    f"No trained model found at {self._model_path}. "
                    f"Call train() first."
                )
            self._pipeline = joblib.load(self._model_path)

    def score_batch(self, texts: list[str]) -> pd.DataFrame:
        """
        Score texts using the trained LogReg pipeline.

        Implementation:
          1. Load pipeline (self._load_pipeline())
          2. probs = self._pipeline.predict_proba(texts)
          3. Identify column indices for 'positive' and 'negative' in
             self._pipeline.classes_
          4. Score = probs[:, pos_idx] - probs[:, neg_idx]
          5. Apply normalize_score() and score_to_label()
          6. Return DataFrame with 'logreg_score' and 'logreg_label'

        Args:
            texts: List of preprocessed headline strings.

        Returns:
            DataFrame with 'logreg_score' (float) and 'logreg_label' (str).

        Raises:
            RuntimeError: If model has not been trained.
        """
        raise NotImplementedError("Implement in Phase 1, Day 3")
