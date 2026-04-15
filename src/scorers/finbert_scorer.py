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
        if self._model is not None:
            return

        cfg = self._scorer_config
        device_str = cfg["device"]

        if device_str == "auto":
            if torch.cuda.is_available():
                self._device = torch.device("cuda")
            elif hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
                self._device = torch.device("mps")
            else:
                self._device = torch.device("cpu")
        else:
            self._device = torch.device(device_str)

        print(f"    Loading FinBERT on {self._device}...")
        self._tokenizer = AutoTokenizer.from_pretrained(cfg["model_name"])
        self._model = AutoModelForSequenceClassification.from_pretrained(cfg["model_name"])
        self._model.to(self._device)
        self._model.eval()

        expected = {0: "positive", 1: "negative", 2: "neutral"}
        actual = self._model.config.id2label
        if actual != expected:
            raise ValueError(
                f"FinBERT label order changed! Expected {expected}, got {actual}. "
                f"Update pos_idx/neg_idx in score_batch."
            )

        print(f"    FinBERT loaded. Labels: {actual}")

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
        self._ensure_loaded()

        batch_size = self._scorer_config["batch_size"]
        all_scores = []

        for i in tqdm(range(0, len(texts), batch_size), desc="FinBERT scoring"):
            batch = texts[i : i + batch_size]
            inputs = self._tokenizer(
                batch,
                return_tensors="pt",
                padding=True,
                truncation=True,
                max_length=512,
            ).to(self._device)

            with torch.no_grad():
                logits = self._model(**inputs).logits

            probs = torch.softmax(logits, dim=1).cpu().numpy()
            # id2label: 0=positive, 1=negative, 2=neutral
            batch_raw = probs[:, 0] - probs[:, 1]
            all_scores.extend(batch_raw)

        results = []
        for raw in all_scores:
            score = normalize_score(float(raw), self.name, self.config)
            label = score_to_label(score, self.config)
            results.append({
                f"{self.name}_score": score,
                f"{self.name}_label": label,
            })
        return pd.DataFrame(results)
