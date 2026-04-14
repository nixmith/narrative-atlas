"""
Score normalization for Narrative Atlas.

Ensures all scorer outputs conform to a unified scale:
  Score: float in [-1.0, +1.0]
  Label: str in {'positive', 'neutral', 'negative'}

Label thresholds are configurable via config.yaml so that all
methods use identical decision boundaries, making inter-method
comparison fair.

Usage:
    from src.normalizer import normalize_score, score_to_label
    score = normalize_score(raw_score, "vader", config)
    label = score_to_label(score, config)
"""


def normalize_score(score: float, method: str, config: dict) -> float:
    """
    Clamp a raw score to the [-1, +1] range.

    Both VADER compound and the P(pos)-P(neg) transformation naturally
    produce [-1, +1], so this is a safety clamp. Logs a warning if
    clamping actually occurs (indicates a bug upstream).

    Args:
        score: Raw sentiment score from a scorer.
        method: Scorer name (for logging).
        config: Loaded config dict.

    Returns:
        Score clamped to [-1.0, +1.0].
    """
    lo, hi = config["normalizer"]["score_range"]
    clamped = max(lo, min(hi, score))
    if clamped != score:
        import logging
        logging.warning(
            f"Score {score} from {method} clamped to {clamped}. "
            f"This may indicate a bug in the scorer."
        )
    return clamped


def score_to_label(score: float, config: dict) -> str:
    """
    Convert a unified score to a categorical label.

    Uses thresholds from config:
      score > positive_threshold  → 'positive'
      score < negative_threshold  → 'negative'
      else                        → 'neutral'

    Args:
        score: Unified score in [-1.0, +1.0].
        config: Loaded config dict.

    Returns:
        One of 'positive', 'neutral', 'negative'.
    """
    pos_thresh = config["normalizer"]["positive_threshold"]
    neg_thresh = config["normalizer"]["negative_threshold"]

    if score > pos_thresh:
        return "positive"
    elif score < neg_thresh:
        return "negative"
    else:
        return "neutral"
