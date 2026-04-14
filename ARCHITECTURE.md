# Narrative Atlas — Architecture Document

This document defines the design decisions, data flow, module responsibilities, and
contracts that govern the Narrative Atlas codebase. Read this before writing or modifying
any code.

---

## 1. Design Principles

### 1.1 Modularity Over Monolith

Every component has a single responsibility and communicates through well-defined
data contracts (DataFrames with specified columns, or typed dataclass instances).
No module reaches into another module's internals.

**Why this matters for Narrative Atlas:** The proof-of-concept implements Layer 4
(public discourse) of the five-layer model. Layers 1–3 and 5 will be added later.
Each new layer needs to plug into the same scoring, normalization, evaluation, and
visualization infrastructure. If the core engine is tightly coupled, every new layer
requires rewriting existing code. If it's modular, each new layer is a new data
loader + new scorer(s), and everything downstream just works.

### 1.2 Configuration Over Constants

Every tunable parameter — file paths, model names, thresholds, hyperparameters,
figure dimensions — lives in `config.yaml`. Source code references these values
through the `config` module. No magic numbers in application code.

**Exception:** Test code may use inline constants for clarity.

### 1.3 Reproducibility

The full pipeline must be reproducible from a single command (`python run_pipeline.py`).
Random seeds are set explicitly. Data splits are deterministic. Model training is
seeded. Figure generation is deterministic. Anyone cloning this repo should get
identical outputs.

### 1.4 Fail Fast, Fail Loud

Validation happens at data boundaries (loading, scoring, merging). If data is
malformed, missing columns, or has unexpected types, raise an exception immediately
with a descriptive message. Don't silently produce wrong results.

---

## 2. Data Flow

The pipeline is a linear DAG. Each stage reads from the previous stage's output
and writes to a well-defined artifact.

```
                    ┌──────────────┐
                    │  config.yaml │
                    └──────┬───────┘
                           │ (read by every module)
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│  STAGE 1: DATA LOADING                                         │
│  Module: src/data_loader.py                                    │
│  Input:  Internet (HuggingFace, Yahoo Finance)                 │
│  Output: data/raw/financial_phrasebank.csv                     │
│          data/raw/aapl_prices.csv                               │
│          Returns: headlines_df, prices_df (+ train/test indices)│
└──────────────────────────────┬──────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────┐
│  STAGE 2: PREPROCESSING                                        │
│  Module: src/preprocessing.py                                  │
│  Input:  headlines_df (raw text + labels)                      │
│  Output: headlines_df with cleaned 'text_clean' column added   │
└──────────────────────────────┬──────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────┐
│  STAGE 3: SCORING                                              │
│  Modules: src/scorers/vader_scorer.py                          │
│           src/scorers/logreg_scorer.py                         │
│           src/scorers/finbert_scorer.py                        │
│  Input:  headlines_df with 'text_clean' column                 │
│  Output: For each scorer, adds two columns to the DataFrame:   │
│          '{method}_score' (float, [-1, +1])                    │
│          '{method}_label' (str, 'positive'|'neutral'|'negative')│
│                                                                │
│  LogReg also outputs: models/logreg_tfidf_pipeline.pkl         │
│                                                                │
│  NOTE: Each scorer calls normalizer.normalize() internally     │
│  to convert its native output to the unified scale.            │
└──────────────────────────────┬──────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────┐
│  STAGE 4: MERGE + EXPORT                                       │
│  Module: run_pipeline.py (orchestrator)                        │
│  Input:  headlines_df with all scorer columns                  │
│  Output: data/processed/headlines_scored.csv                   │
│                                                                │
│  Master CSV columns:                                           │
│    text           — original headline text                     │
│    text_clean     — preprocessed text                          │
│    true_label     — expert-annotated label                     │
│    split          — 'train' or 'test'                         │
│    vader_score    — VADER unified score [-1, +1]               │
│    vader_label    — VADER predicted label                      │
│    logreg_score   — LogReg unified score [-1, +1]              │
│    logreg_label   — LogReg predicted label                     │
│    finbert_score  — FinBERT unified score [-1, +1]             │
│    finbert_label  — FinBERT predicted label                    │
└──────────────────────────────┬──────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────┐
│  STAGE 5: EVALUATION                                           │
│  Module: src/evaluation.py                                     │
│  Input:  headlines_scored.csv (test split only for classif.)   │
│  Output: Printed summary table                                 │
│          Returns: dict of all metrics                          │
│                                                                │
│  Metrics computed:                                             │
│    Per method: accuracy, precision, recall, F1 (per-class +    │
│                macro), on test split only                      │
│    Per method pair: Cohen's κ (on full dataset)                │
│    Confusion matrices: 3x3 per method                          │
└──────────────────────────────┬──────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────┐
│  STAGE 6: TEMPORAL ANALYSIS                                    │
│  Module: src/temporal.py                                       │
│  Input:  headlines_scored.csv + aapl_prices.csv                │
│  Output: data/processed/weekly_aggregated.csv                  │
│                                                                │
│  Weekly CSV columns:                                           │
│    week_start     — Monday of each week                        │
│    volume         — article count that week                    │
│    vader_mean     — mean VADER score that week                 │
│    logreg_mean    — mean LogReg score that week                │
│    finbert_mean   — mean FinBERT score that week               │
│    finbert_std    — std dev of FinBERT scores (for scatter)    │
│    weekly_return  — (close_friday - close_prev_friday) / close │
│    next_return    — next week's return (shifted forward by 1)  │
│                                                                │
│  Also computes: Pearson r, Spearman ρ for each method's       │
│  weekly mean vs. next-week return                              │
└──────────────────────────────┬──────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────┐
│  STAGE 7: VISUALIZATION                                        │
│  Module: src/visualizations.py                                 │
│  Input:  headlines_scored.csv, weekly_aggregated.csv            │
│  Output: figures/fig1_sentiment_timeline.png                   │
│          figures/fig2_sentiment_distributions.png               │
│          figures/fig3_method_agreement.png                      │
│          figures/fig4_keyword_spectrogram.png                   │
│          figures/fig5_volume_sentiment_scatter.png              │
│                                                                │
│  All figures: 300 DPI, tight_layout, consistent color scheme   │
└─────────────────────────────────────────────────────────────────┘
```

---

## 3. Configuration Schema

```yaml
# config.yaml

project:
  name: "Narrative Atlas"
  random_seed: 42

data:
  fpb_config: "sentences_50agree"     # FinancialPhraseBank agreement threshold
  test_size: 0.20                      # Train/test split ratio
  ticker: "AAPL"                       # Stock ticker for price data
  price_start: "2020-01-01"           # Price data date range
  price_end: "2025-12-31"
  paths:
    raw_headlines: "data/raw/financial_phrasebank.csv"
    raw_prices: "data/raw/aapl_prices.csv"
    scored_headlines: "data/processed/headlines_scored.csv"
    weekly_aggregated: "data/processed/weekly_aggregated.csv"

preprocessing:
  lowercase: true
  remove_punctuation: false            # Keep punctuation — VADER uses it
  remove_numbers: false                # Keep numbers — financial text needs them
  min_token_length: 1

scorers:
  vader:
    enabled: true
    name: "vader"
  logreg:
    enabled: true
    name: "logreg"
    max_features: 10000
    ngram_range: [1, 2]
    max_iter: 1000
    class_weight: "balanced"
    model_path: "models/logreg_tfidf_pipeline.pkl"
  finbert:
    enabled: true
    name: "finbert"
    model_name: "ProsusAI/finbert"
    batch_size: 16
    device: "auto"                     # "auto", "cpu", "cuda", or "mps"

normalizer:
  score_range: [-1.0, 1.0]
  positive_threshold: 0.1             # score > 0.1 → positive
  negative_threshold: -0.1            # score < -0.1 → negative

evaluation:
  metrics: ["accuracy", "f1_macro", "f1_per_class", "cohens_kappa"]
  correlation_methods: ["pearson", "spearman"]

visualization:
  dpi: 300
  figsize_timeline: [10, 4]
  figsize_distributions: [8, 4]
  figsize_agreement: [6, 5]
  figsize_spectrogram: [10, 5]
  figsize_scatter: [7, 5]
  rolling_window: 7                    # Days for rolling average
  colors:
    vader: "#D85A30"                   # Coral
    logreg: "#1D9E75"                  # Teal
    finbert: "#3266AD"                 # Blue
    price: "#888888"
    positive: "#1D9E75"
    negative: "#E24B4A"
  output_dir: "figures"
```

---

## 4. Module Contracts

### 4.1 src/config.py

**Responsibility:** Load `config.yaml`, expose as a nested dictionary or dataclass.
Provide accessor functions for common paths and parameters.

**Public interface:**
```python
def load_config(path: str = "config.yaml") -> dict
def get_scorer_config(scorer_name: str) -> dict
def get_path(key: str) -> Path
```

### 4.2 src/data_loader.py

**Responsibility:** Download (if needed) and load FinancialPhraseBank and price data.
Produce clean DataFrames with deterministic train/test splits.

**Public interface:**
```python
def load_headlines(config: dict) -> pd.DataFrame
    """
    Returns DataFrame with columns:
      text: str         — raw headline
      true_label: str   — 'positive', 'neutral', or 'negative'
      split: str        — 'train' or 'test'
    """

def load_prices(config: dict) -> pd.DataFrame
    """
    Returns DataFrame with columns:
      date: datetime     — trading date
      close: float       — adjusted close price
    Indexed by date.
    """
```

**Validation on output:**
- `text` column has no nulls, no empty strings
- `true_label` values are exactly {'positive', 'neutral', 'negative'}
- `split` values are exactly {'train', 'test'}
- Label distribution in test split roughly mirrors train split (stratified)

### 4.3 src/preprocessing.py

**Responsibility:** Clean and normalize raw headline text. Operates in-place on
a DataFrame, adding a `text_clean` column.

**Public interface:**
```python
def preprocess(df: pd.DataFrame, config: dict) -> pd.DataFrame
    """
    Input:  DataFrame with 'text' column
    Output: Same DataFrame with 'text_clean' column added.

    Steps:
      1. Strip leading/trailing whitespace
      2. Normalize unicode (NFKD)
      3. Optionally lowercase (config-driven)
      4. Collapse multiple spaces to single
      5. Remove empty results → raise if any

    Does NOT remove punctuation or numbers by default —
    VADER uses punctuation signals, financial text needs numbers.
    """
```

**Design note:** Preprocessing is deliberately minimal for this domain. Financial
headlines are already clean, short, and well-formatted. Aggressive preprocessing
(stemming, stopword removal) would harm FinBERT and potentially VADER. The
`text_clean` column exists to guarantee consistent whitespace and encoding, not
to aggressively transform the text.

### 4.4 src/scorers/base.py

**Responsibility:** Define the abstract interface all scorers must implement.

```python
from abc import ABC, abstractmethod
import pandas as pd

class BaseScorer(ABC):
    """
    Abstract base class for all sentiment scorers.

    Every scorer must:
    1. Accept a config dict at initialization
    2. Implement score_batch() to score a list of texts
    3. Return results as a DataFrame with exactly two columns:
       '{name}_score' (float in [-1, +1]) and '{name}_label' (str)

    The name property identifies the scorer and determines column names.
    """

    def __init__(self, config: dict):
        self.config = config

    @property
    @abstractmethod
    def name(self) -> str:
        """Short identifier used in column names: 'vader', 'logreg', 'finbert'"""
        ...

    @abstractmethod
    def score_batch(self, texts: list[str]) -> pd.DataFrame:
        """
        Score a list of texts.

        Args:
            texts: List of preprocessed headline strings.

        Returns:
            DataFrame with len(texts) rows and exactly two columns:
              '{self.name}_score': float in [-1.0, +1.0]
              '{self.name}_label': str in {'positive', 'neutral', 'negative'}
        """
        ...

    def score_dataframe(self, df: pd.DataFrame, text_col: str = "text_clean") -> pd.DataFrame:
        """
        Score all rows in a DataFrame. Adds score and label columns in-place.

        This method is provided by the base class — subclasses do NOT override it.
        It calls score_batch() internally and handles merging.
        """
        results = self.score_batch(df[text_col].tolist())
        df[f"{self.name}_score"] = results[f"{self.name}_score"].values
        df[f"{self.name}_label"] = results[f"{self.name}_label"].values
        return df
```

**Why this pattern matters:** When Narrative Atlas expands beyond finance, new
scorers (e.g., a geopolitical framing classifier, an aspect-based model) implement
the same interface. The pipeline, evaluation, and visualization code never change —
they operate on `{method}_score` and `{method}_label` columns regardless of which
scorer produced them.

### 4.5 src/scorers/vader_scorer.py

**Responsibility:** Score texts using VADER compound score.

**Implementation notes:**
- Uses `vaderSentiment.SentimentIntensityAnalyzer`
- Native output is compound score already in [-1, +1] — no normalization needed
- Label thresholds from config (default: > 0.1 positive, < -0.1 negative)
- No training required

### 4.6 src/scorers/logreg_scorer.py

**Responsibility:** Score texts using a TF-IDF + Logistic Regression pipeline.

**Implementation notes:**
- Uses `sklearn.pipeline.Pipeline` with `TfidfVectorizer` + `LogisticRegression`
- Must support two modes: `train()` and `score_batch()`
- `train()` fits the pipeline on training data, saves to `models/` via joblib
- `score_batch()` loads the saved pipeline and predicts
- Score normalization: `P(positive) - P(negative)` from `predict_proba()`
- Hyperparameters from config (max_features, ngram_range, max_iter, class_weight)

**Additional interface beyond BaseScorer:**
```python
def train(self, texts: list[str], labels: list[str]) -> None:
    """Fit the TF-IDF + LogReg pipeline and save to disk."""

def is_trained(self) -> bool:
    """Check if a saved model exists."""
```

### 4.7 src/scorers/finbert_scorer.py

**Responsibility:** Score texts using the pretrained ProsusAI/finbert model.

**Implementation notes:**
- Uses `transformers.AutoTokenizer` + `AutoModelForSequenceClassification`
- Batch inference for efficiency (batch_size from config)
- Device auto-detection: CUDA → MPS → CPU
- Score normalization: softmax → `P(positive) - P(negative)`
- Label order for ProsusAI/finbert is [positive, negative, neutral] — verify this
  at initialization and raise if model config disagrees
- Progress bar for batch inference (tqdm)

### 4.8 src/normalizer.py

**Responsibility:** Convert native scorer outputs to the unified [-1, +1] score
and categorical label.

**Public interface:**
```python
def normalize_score(score: float, method: str, config: dict) -> float:
    """Ensure score is in [-1, +1]. Clip if necessary."""

def score_to_label(score: float, config: dict) -> str:
    """
    Apply thresholds from config:
      score > positive_threshold  → 'positive'
      score < negative_threshold  → 'negative'
      else                        → 'neutral'
    """
```

**Design note:** VADER and the P(pos)-P(neg) transformation both naturally produce
[-1, +1] scores, so normalization is mostly a safety clamp. The thresholded label
mapping ensures all three methods use identical decision boundaries, making
inter-method comparison fair.

### 4.9 src/evaluation.py

**Responsibility:** Compute all classification and agreement metrics.

**Public interface:**
```python
def evaluate_classifier(
    true_labels: list[str],
    predicted_labels: list[str],
    method_name: str
) -> dict:
    """
    Returns dict with:
      'accuracy': float
      'classification_report': dict (from sklearn, includes per-class P/R/F1)
      'confusion_matrix': np.ndarray (3x3)
    """

def evaluate_agreement(
    labels_a: list[str],
    labels_b: list[str],
    name_a: str,
    name_b: str
) -> dict:
    """
    Returns dict with:
      'pair': str (e.g., 'vader_vs_logreg')
      'agreement_pct': float
      'cohens_kappa': float
    """

def evaluate_all(df: pd.DataFrame, config: dict) -> dict:
    """
    Run all evaluations on the scored DataFrame.
    Returns nested dict with per-method and per-pair metrics.
    Also prints a formatted summary table to stdout.
    """
```

### 4.10 src/temporal.py

**Responsibility:** Aggregate scored headlines into weekly time series and compute
sentiment-return correlations.

**Public interface:**
```python
def assign_dates(df: pd.DataFrame, config: dict) -> pd.DataFrame:
    """
    Assign pseudo-dates to headlines for temporal analysis.

    Strategy: Distribute headlines evenly across the price data date range.
    This is a simplification — real Narrative Atlas would use actual
    publication timestamps. For the proof-of-concept, this enables
    temporal visualization and correlation analysis.

    Adds 'date' column to DataFrame.
    """

def aggregate_weekly(df: pd.DataFrame, prices_df: pd.DataFrame) -> pd.DataFrame:
    """
    Group headlines by week. Compute:
      - volume (count)
      - mean and std of each method's score
      - weekly stock return
      - next-week return (shifted)

    Returns weekly_df saved to data/processed/weekly_aggregated.csv
    """

def compute_correlations(weekly_df: pd.DataFrame, config: dict) -> dict:
    """
    Pearson and Spearman correlation between each method's weekly
    sentiment mean and next-week return.

    Returns dict of {method: {pearson_r, pearson_p, spearman_rho, spearman_p}}
    """
```

### 4.11 src/visualizations.py

**Responsibility:** Generate all five figures. Each figure is a standalone function
that reads from the processed data files and writes a PNG to `figures/`.

**Public interface:**
```python
def setup_style(config: dict) -> None:
    """Set matplotlib rcParams for consistent styling across all figures."""

def fig1_sentiment_timeline(df: pd.DataFrame, prices: pd.DataFrame, config: dict) -> None
def fig2_sentiment_distributions(df: pd.DataFrame, config: dict) -> None
def fig3_method_agreement(df: pd.DataFrame, config: dict) -> None
def fig4_keyword_spectrogram(df: pd.DataFrame, config: dict) -> None
def fig5_volume_sentiment_scatter(weekly_df: pd.DataFrame, config: dict) -> None

def generate_all_figures(config: dict) -> None:
    """Load data and generate all figures. Called by run_pipeline.py."""
```

**Color consistency:** All figures use the same colors for the same methods.
Colors are defined in `config.yaml` and accessed through `config['visualization']['colors']`.
VADER is always coral (#D85A30), LogReg is always teal (#1D9E75), FinBERT is
always blue (#3266AD).

---

## 5. Extension Points (Future Narrative Atlas Layers)

The architecture is designed so that adding a new signal layer requires:

1. **A new data loader function** in `data_loader.py` (or a new loader module
   for complex sources like SEC EDGAR)
2. **A new scorer subclass** if the layer requires custom NLP (e.g., an aspect-based
   sentiment scorer, an embedding drift detector)
3. **A new visualization function** in `visualizations.py`
4. **Config entries** in `config.yaml` for any new parameters

Nothing in the existing pipeline, evaluation, or normalization code needs to change.
The `BaseScorer` interface and the `{method}_score` / `{method}_label` column
convention ensure that new scorers plug in seamlessly.

### Planned future scorers (not implemented in proof-of-concept):
- `EmbeddingDriftScorer` — track centroid shift in filing language over time (Layer 1)
- `InsiderDivergenceScorer` — compare executive statement sentiment to trade direction (Layer 2)
- `AspectSentimentScorer` — extract *what aspect* sentiment is about (Layer 3)
- `FrameClassifier` — classify which narrative frame a text uses (cross-domain)

---

## 6. Testing Strategy

Tests are organized by module, not by test type. Each test file tests the
corresponding source module.

**Levels:**
- **Unit tests**: Test individual functions with small synthetic inputs.
  All tests in `tests/` are unit tests for the proof-of-concept.
- **Integration tests** (future): Test the full pipeline end-to-end on a
  small subset of real data.

**Fixtures:** `conftest.py` provides:
- `sample_headlines`: A small DataFrame (20 rows) with known labels for deterministic testing
- `sample_prices`: A small price DataFrame (60 trading days)
- `sample_config`: A test configuration dict with paths pointing to temp directories

**Key testing principle:** Scorers are tested for *contract compliance*
(correct column names, correct value ranges, correct types), not for
*accuracy on real data*. Accuracy is measured by `evaluation.py` at runtime,
not by unit tests.
