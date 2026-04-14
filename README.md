# Narrative Atlas

**A multi-method NLP pipeline for financial sentiment analysis and temporal visualization.**

Narrative Atlas is the core engine of a larger narrative intelligence platform. It ingests
financial news text, applies three sentiment analysis methods of increasing sophistication
(lexicon-based → classical ML → pretrained transformer), evaluates them rigorously against
expert-labeled ground truth, and produces publication-quality visualizations that reveal how
sentiment evolves over time and across methods.

This repository contains the proof-of-concept implementation focused on financial news,
built as part of CSCI 4535/5535 Natural Language Processing coursework. The architecture
is designed to be modular and extensible — adding new scorers, data sources, or
visualization types requires implementing a single interface.

---

## Quick Start

```bash
# 1. Clone and enter the repo
git clone <repo-url>
cd narrative-atlas

# 2. Create a virtual environment (recommended)
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Run the full pipeline
python run_pipeline.py
```

This will:
1. Download FinancialPhraseBank and AAPL price data (first run only)
2. Score all headlines with VADER, Logistic Regression, and FinBERT
3. Train and save the LogReg model
4. Compute evaluation metrics and print a summary table
5. Generate all figures to `figures/`

---

## Project Structure

```
narrative-atlas/
│
├── README.md                  # You are here
├── ARCHITECTURE.md            # Design decisions, data flow, module contracts
├── requirements.txt           # Python dependencies
├── config.yaml                # All configurable parameters (paths, model names, thresholds)
├── run_pipeline.py            # Entry point — runs full pipeline end-to-end
│
├── data/
│   ├── raw/                   # Untouched downloaded data (gitignored)
│   │   ├── financial_phrasebank.csv
│   │   └── aapl_prices.csv
│   └── processed/             # Pipeline outputs (gitignored)
│       ├── headlines_scored.csv       # Master file: all headlines + all method scores
│       └── weekly_aggregated.csv      # Weekly sentiment + volume + returns
│
├── models/
│   └── logreg_tfidf_pipeline.pkl      # Trained LogReg model (gitignored)
│
├── figures/                   # Generated visualizations (gitignored)
│   ├── fig1_sentiment_timeline.png
│   ├── fig2_sentiment_distributions.png
│   ├── fig3_method_agreement.png
│   ├── fig4_keyword_spectrogram.png
│   └── fig5_volume_sentiment_scatter.png
│
├── src/                       # Source code
│   ├── __init__.py
│   ├── config.py              # Configuration loader + constants
│   ├── data_loader.py         # Download + load + split datasets
│   ├── preprocessing.py       # Text cleaning and normalization
│   ├── normalizer.py          # Unify all scorer outputs to [-1, +1]
│   ├── evaluation.py          # Classification metrics + correlation analysis
│   ├── temporal.py            # Weekly aggregation + sentiment-return alignment
│   ├── visualizations.py      # All figure generation functions
│   └── scorers/               # Sentiment scoring methods (pluggable)
│       ├── __init__.py
│       ├── base.py            # Abstract base class for all scorers
│       ├── vader_scorer.py    # VADER lexicon-based sentiment
│       ├── logreg_scorer.py   # TF-IDF + Logistic Regression
│       └── finbert_scorer.py  # Pretrained FinBERT transformer
│
├── tests/                     # Test suite
│   ├── conftest.py            # Shared fixtures (sample data, mock scorers)
│   ├── test_data_loader.py
│   ├── test_preprocessing.py
│   ├── test_scorers.py
│   ├── test_normalizer.py
│   ├── test_evaluation.py
│   └── test_temporal.py
│
├── notebooks/                 # Exploration and prototyping (optional)
│   └── exploration.ipynb
│
└── report/                    # Final report files
    └── NarrativeAtlas_FinalReport.pdf
```

---

## Configuration

All tunable parameters live in `config.yaml`. No magic numbers in source code.
See `ARCHITECTURE.md` §3 for the full configuration schema.

---

## Data

**FinancialPhraseBank** (Malo et al., 2014): ~4,845 financial news sentences labeled
positive/neutral/negative by domain experts. Downloaded automatically on first run.

**AAPL Price Data**: Daily OHLCV from Yahoo Finance via `yfinance`. Downloaded
automatically on first run.

Raw data is stored in `data/raw/` and never modified. Processed outputs go to
`data/processed/`. Both directories are gitignored — the pipeline regenerates
everything from scratch.

---

## Scorers

Each scorer implements the `BaseScorer` interface (see `src/scorers/base.py`):

| Scorer | Type | Training | Course Connection |
|--------|------|----------|-------------------|
| VADER | Lexicon + rules | None (pretrained lexicon) | Ch 4: Sentiment lexicons |
| LogReg | TF-IDF + classifier | Trained on FPB train split | Ch 4: Classification, Ch 5: TF-IDF |
| FinBERT | Pretrained transformer | None (pretrained) | Ch 5–7: Embeddings, neural nets |

Adding a new scorer: create a new file in `src/scorers/`, subclass `BaseScorer`,
implement `score()` and `score_batch()`, register it in `config.yaml`.

---

## Evaluation

- **Classification**: Accuracy, Precision, Recall, F1 (per-class and macro) on held-out test set
- **Inter-method agreement**: Cohen's κ for all scorer pairs
- **Temporal correlation**: Pearson r and Spearman ρ between weekly sentiment and next-week returns

---

## Figures

| # | Name | What It Shows |
|---|------|---------------|
| 1 | Sentiment Timeline | Three method traces + price overlay, annotated events |
| 2 | Sentiment Distributions | Violin plots comparing score distributions per method |
| 3 | Method Agreement | 3×3 heatmap of pairwise agreement + Cohen's κ |
| 4 | Keyword Spectrogram | TF-IDF top terms × time heatmap |
| 5 | Volume-Sentiment Scatter | Weekly volume vs. sentiment, colored by next-week return |

---

## Testing

```bash
# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=src --cov-report=term-missing
```

---

## References

1. Malo, P. et al. (2014). Good debt or bad debt: Detecting semantic orientations in economic texts. *JASIST*, 65(4).
2. Araci, D. (2019). FinBERT: Financial sentiment analysis with pre-trained language models. *arXiv:1908.10063*.
3. Hutto, C. J. & Gilbert, E. (2014). VADER: A parsimonious rule-based model for sentiment analysis of social media text. *ICWSM*.
4. Loughran, T. & McDonald, B. (2011). When is a liability not a liability? *Journal of Finance*, 66(1).
5. Jurafsky, D. & Martin, J. H. (2024). *Speech and Language Processing*, 3rd ed. draft, Ch. 4–7.
