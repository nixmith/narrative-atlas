"""
VADER sentiment scorer for Narrative Atlas.

Uses the VADER (Valence Aware Dictionary and sEntiment Reasoner) model,
a rule-based sentiment analyzer combining a curated lexicon with
grammatical heuristics for negation, intensification, and punctuation.

Course connection: Chapter 4 — sentiment lexicons (MPQA, General Inquirer).
VADER is the modern production-grade descendant of these approaches.

Properties:
  - No training required (pretrained lexicon)
  - Native output: compound score in [-1, +1]
  - Handles informal text, punctuation, capitalization
  - NOT domain-adapted for finance (this is the point — it's the baseline)
"""

import pandas as pd
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

from src.scorers.base import BaseScorer
from src.normalizer import normalize_score, score_to_label


class VaderScorer(BaseScorer):
    """
    Lexicon-based sentiment scorer using VADER.

    The compound score is already in [-1, +1], so normalization
    is just a safety clamp. Labels use the configurable thresholds
    from config['normalizer'].
    """

    def __init__(self, config: dict):
        super().__init__(config)
        self._analyzer = SentimentIntensityAnalyzer()

    @property
    def name(self) -> str:
        return "vader"

    def score_batch(self, texts: list[str]) -> pd.DataFrame:
        """
        Score texts using VADER compound score.

        Implementation:
          1. For each text, call self._analyzer.polarity_scores(text)
          2. Extract the 'compound' score (already in [-1, +1])
          3. Apply normalize_score() as safety clamp
          4. Apply score_to_label() using config thresholds
          5. Return DataFrame with '{name}_score' and '{name}_label'

        Args:
            texts: List of preprocessed headline strings.

        Returns:
            DataFrame with 'vader_score' (float) and 'vader_label' (str).
        """
        scores = []
        for text in texts:
            vs = self._analyzer.polarity_scores(text)
            raw = vs["compound"]
            score = normalize_score(raw, self.name, self.config)
            label = score_to_label(score, self.config)
            scores.append({
                f"{self.name}_score": score,
                f"{self.name}_label": label,
            })
        return pd.DataFrame(scores)
