"""
Sentiment scorers for Narrative Atlas.

Each scorer implements the BaseScorer interface, producing standardized
'{method}_score' and '{method}_label' columns. Scorers are pluggable —
new methods are added by subclassing BaseScorer.

Available scorers:
    VaderScorer   — Lexicon-based (no training required)
    LogRegScorer  — TF-IDF + Logistic Regression (requires training)
    FinBERTScorer — Pretrained transformer (no training required)
"""

from src.scorers.base import BaseScorer
from src.scorers.vader_scorer import VaderScorer
from src.scorers.logreg_scorer import LogRegScorer
from src.scorers.finbert_scorer import FinBERTScorer

__all__ = ["BaseScorer", "VaderScorer", "LogRegScorer", "FinBERTScorer"]
