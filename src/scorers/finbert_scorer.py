"""
FinBERT sentiment scorer for Narrative Atlas.

Uses ProsusAI/finbert, a BERT model fine-tuned on financial communication
text for three-class sentiment classification (positive/negative/neutral).

Course connection:
  - Chapter 5: Word embeddings and contextual representations
  - Chapter 6: Neural network fundamentals
  - Chapter 7: Large language models and transformers

Properties:
  - No training required (pretrained + fine-tuned)
  - Contextual embeddings capture domain-specific semantics
  - Score: P(positive) - P(negative) from softmax outputs
  - Slowest of the three methods — batch inference with progress bar
  - Automatic device detection: CUDA → MPS → CPU
"""

import pandas as pd
import numpy as np
from tqdm import tqdm
import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification

from src.scorers.base import BaseScorer
from src.normalizer import normalize_score, score_to_label


class FinBERTScorer(BaseScorer):
    """
    Pretrained FinBERT transformer scorer.

    Loads the model and tokenizer on first use (lazy initialization).
    The model is ~400MB and is cached by HuggingFace after first download.

    IMPORTANT: The label order for ProsusAI/finbert is:
      model.config.id2label = {0: 'positive', 1: 'negative', 2: 'neutral'}
    Verify this at initialization. If it changes in a future model version,
    the score computation will be wrong.
    """

    def __init__(self, config: dict):
        super().__init__(config)
        self._scorer_config = config["scorers"]["finbert"]
        self._tokenizer = None
        self._model = None
        self._device = None

    @property
    def name(self) -> str:
        return "finbert"

    def _ensure_loaded(self) -> None:
        """
        Lazy-load model and tokenizer on first use.

        Implementation:
          1. If already loaded, return immediately
          2. Determine device:
             - config device == "auto": try CUDA, then MPS, then CPU
             - Otherwise use the configured device string
          3. Load tokenizer: AutoTokenizer.from_pretrained(model_name)
          4. Load model: AutoModelForSequenceClassification.from_pretrained(model_name)
          5. Move model to device, set to eval mode
          6. Verify label order: model.config.id2label should map
             0 → 'positive', 1 → 'negative', 2 → 'neutral'
             If not, raise ValueError with the actual mapping
          7. Print: "FinBERT loaded on {device}"
        """
        raise NotImplementedError("Implement in Phase 1, Day 4")

    def score_batch(self, texts: list[str]) -> pd.DataFrame:
        """
        Score texts using FinBERT with batched inference.

        Implementation:
          1. self._ensure_loaded()
          2. Process texts in batches of config batch_size
          3. For each batch:
             a. tokenizer(batch, return_tensors="pt", padding=True,
                          truncation=True, max_length=512)
             b. Move inputs to device
             c. with torch.no_grad(): outputs = model(**inputs)
             d. probs = torch.softmax(outputs.logits, dim=1)
             e. Extract P(positive) and P(negative) using verified indices
             f. score = P(positive) - P(negative)
          4. Collect all scores
          5. Apply normalize_score() and score_to_label()
          6. Show tqdm progress bar across batches
          7. Return DataFrame with 'finbert_score' and 'finbert_label'

        Args:
            texts: List of preprocessed headline strings.

        Returns:
            DataFrame with 'finbert_score' (float) and 'finbert_label' (str).
        """
        raise NotImplementedError("Implement in Phase 1, Day 4")
