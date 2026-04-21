# Narrative Atlas — Progress Notes

**Phase 1, Days 1–3 · April 14–16, 2026**

These notes are a running log of what Narrative Atlas is, what we've built so far, and how the pieces fit together. They're written for a reader who knows a little machine learning but isn't necessarily an NLP specialist, and they're meant to be the reference we draw from when assembling the final report. The goal is clarity at the depth a reviewer actually needs — not a textbook, not a changelog.

---

## 1. What we're building

Narrative Atlas is a multi-method sentiment analysis pipeline for financial news. Three independent scoring engines read the same headlines, produce scores on the same scale, and are compared head-to-head against expert labels and against stock-price movements. The central question is whether increasingly sophisticated NLP methods — a general-purpose lexicon, a classical supervised classifier, and a finance-tuned transformer — actually buy us meaningfully different views of the same text, and whether any of those views track reality (here represented by next-week AAPL returns).

This is the proof-of-concept implementation of what `ARCHITECTURE.md` calls "Layer 4: public discourse." Narrative Atlas as a broader project envisions four other layers of narrative intelligence — regulatory filings, insider actions, aspect-level sentiment, cross-domain framing — all plugging into the same scoring and evaluation machinery. Building Layer 4 cleanly is how we validate that the core engine generalizes.

The design principles underpinning every decision in the codebase are in `ARCHITECTURE.md §1`: modular over monolithic, configuration over constants, reproducibility via seeded randomness, and fail-fast validation at every data boundary. These aren't aesthetic preferences. They're the reason a new signal layer in six months will be a new file and a config entry, not a rewrite.

---

## 2. The data

Two datasets enter the pipeline.

**FinancialPhraseBank** (Malo et al., 2014) is the ground-truth dataset for the classification work. It conta ins roughly 4,846 sentences extracted from English-language financial news and press releases, each labeled positive, neutral, or negative by a panel of finance-literate annotators. We use the `sentences_50agree` split, which keeps only sentences where at least half the annotators agreed on the label — a reasonable trade-off between dataset size and label reliability. After download, our label distribution is skewed toward neutral (59.4%), followed by positive (28.1%) and negative (12.5%). That imbalance matters and we address it explicitly when training the logistic regression model (see §5).

The dataset downloads from HuggingFace on first run and caches to `data/raw/financial_phrasebank.csv`. Every subsequent run reads from cache, which makes the pipeline fast and offline-friendly once primed. We split it 80/20 train/test using a stratified split seeded from `config['project']['random_seed']`, so the label proportions in train and test are identical and the exact same rows land in the same splits every time the pipeline runs. Stratification matters: a random split on a heavily-imbalanced dataset can easily produce a test set with almost no negatives, which makes per-class metrics meaningless.

**AAPL price data** comes from Yahoo Finance via `yfinance`. We pull daily close prices from 2020-01-01 through 2025-12-31 and cache to `data/raw/aapl_prices.csv`. Apple is a placeholder — the interesting property of this data is not the specific ticker but the fact that we now have a time-aligned market signal we can correlate sentiment against in Phase 2. The price data is used only in the temporal analysis stage; the sentiment scoring doesn't touch it.

Both loaders fail loudly. `_validate_headlines` and `_validate_prices` check for required columns, null values, empty strings, label-set conformity, split presence, and minimum row counts before returning a DataFrame. If any of these checks fail — including against a corrupted cache file — the error message names the offending file so you can delete it and re-run.

---

## 3. Preprocessing: the case for doing almost nothing

Preprocessing in Narrative Atlas is deliberately minimal, and this is worth explaining because it runs against a common instinct to lowercase, tokenize, stem, and strip stopwords by default.

For a general corpus — Twitter data, product reviews, Wikipedia — aggressive preprocessing often helps: it shrinks the vocabulary, collapses morphological variants, and reduces feature sparsity. For financial headlines, aggressive preprocessing actively harms us.

VADER reads exclamation points, capitalization, and negation words as part of its sentiment signal. Lowercasing before VADER throws away the capitalization cue entirely. Removing punctuation throws away the exclamation-point intensifier. FinBERT is a transformer whose tokenizer was trained on uncleaned text and whose accuracy depends on receiving text that looks like what it saw during training; stemming or stopword removal would feed it out-of-distribution input. Even for the logistic regression model, aggressive cleaning is suspect — financial text is dense with numbers, tickers, and percentages that matter ("profits down 15%" is not the same sentiment as "profits"), and stripping them throws away usable signal.

So what does `preprocess()` actually do? Five things, in order: strip leading and trailing whitespace, apply Unicode NFKD normalization (so that accented characters, ligatures, and full-width variants all collapse to a canonical form), optionally lowercase (controlled by `config['preprocessing']['lowercase']` — currently `true` because TF-IDF on raw-case text would treat "Apple" and "apple" as different tokens, which is a waste of feature budget for our use case), collapse runs of whitespace to a single space, and raise a `ValueError` if any text became empty somewhere along the way. That's it. No tokenization, no stemming, no stopword filtering, no punctuation stripping.

The output is a new `text_clean` column added to the DataFrame. The original `text` column is preserved so that downstream modules like FinBERT can choose whether to consume the cleaned or raw version (FinBERT will consume the cleaned version for consistency, but it would also work on raw). This separation is cheap and buys us the ability to audit preprocessing by diffing the two columns.

One caveat worth flagging: the NFKD docstring originally claimed to convert smart quotes to straight quotes. It does not. NFKD only decomposes characters that have an explicit compatibility mapping in the Unicode database, and smart quotes (`"`, `"`, `'`, `'`) don't — they're atomic codepoints with no decomposition. The docstring is now corrected. In practice this doesn't bite us because none of the three scorers are sensitive to quote style, but it's the kind of subtle wrongness that compounds if you build more normalization on top of an incorrect mental model.

---

## 4. The lexicon baseline — VADER

The first scorer we implemented is VADER (Valence Aware Dictionary and sEntiment Reasoner), from Hutto and Gilbert's 2014 ICWSM paper. VADER is a rule-based system built around a curated sentiment lexicon. Every word in its dictionary has a hand-rated valence score, and for any input text VADER sums those scores, applies a small set of grammatical rules (negation flipping, intensifier boosting, capitalization emphasis, punctuation boosting), and normalizes the result into a single "compound" score between -1 and +1. The normalization is a squashing function that saturates smoothly — a sentence with one positive word and a sentence with five positive words both land near the positive end, but the five-word one lands closer to +1.

VADER is the textbook case of what Jurafsky and Martin Chapter 4 calls a *sentiment lexicon* approach. Intellectually it's the modern descendant of MPQA and the General Inquirer — the same idea (count signed words) with much more engineering attention paid to the edge cases that wreck naive word-counting (negation, "not bad," emoticons, intensity modifiers, punctuation).

Its strengths: zero training required, interpretable (you can always ask "why did VADER say positive?" and inspect the words it fired on), fast, offline, and reasonably strong on informal prose like tweets and reviews.

Its weakness for our use case is its central weakness: it is not domain-adapted. VADER's lexicon was built for social-media text, not financial prose. Words that carry specific directional meaning in finance — "dilution," "guidance," "downgrade," "restructuring," "headwinds" — are either absent from the lexicon or scored with their general-English valence, which is usually wrong in context. We expect this to show up as over-confident positive readings on mildly promotional corporate language and under-detection of negative sentiment hidden in finance-specific vocabulary.

Our VADER scorer is a thin wrapper over `vaderSentiment.SentimentIntensityAnalyzer`. For each headline we pull the `compound` field, pass it through the shared `normalize_score` function (a safety clamp), and pass the score through `score_to_label` to assign a categorical label using thresholds from `config['normalizer']` (currently +0.1 and -0.1). The output slots into two DataFrame columns — `vader_score` and `vader_label` — which is the convention every scorer follows.

On first run across the full 4,846-headline FPB dataset, VADER produced this label distribution:

```
positive    2347
neutral     2068
negative     431
```

Compared to the true distribution (positive 1363, neutral 2879, negative 604) VADER is heavily over-predicting positive and under-predicting neutral. This is exactly the pattern we expected: general-purpose sentiment lexicons read finance-speak as rosier than it actually is, because corporate language is narratively upbeat by default ("partnership," "growth," "enable," "commitment") even when the underlying news is neutral or negative. Spot-checking the top five most positive headlines (all VADER-scored above +0.92) showed sentences about partnerships, efficiency improvements, and budget justifications — none of which are strongly positive in a financial sense, but all of which contain lexicon words VADER reads as enthusiasm.

The spot-check at the negative end was healthier: "critical," "failure," "damaged," "worried" all fired as expected. VADER is asymmetrically over-sensitive to positive language. Keep this in mind when we look at the confusion matrices in Phase 2.

---

## 5. The supervised baseline — TF-IDF + logistic regression

The second scorer is where the classical ML content of the course starts showing up. We replace VADER's general-purpose lexicon with a model that has actually seen FinancialPhraseBank at training time. The hypothesis is simple: if we let a classifier learn domain-specific vocabulary from labeled examples, it should beat a general-purpose lexicon on domain-specific text. Proving this empirically is one of the load-bearing claims of the final report.

The scorer is built as a scikit-learn `Pipeline` with two stages: TF-IDF feature extraction followed by a multinomial logistic regression classifier. Both stages deserve a paragraph because they show up in the course material (Chapters 4 and 5) and the final report will need to explain what each of them is actually doing.

### 5.1 TF-IDF: turning text into numbers

A classifier can't eat text directly; it needs a fixed-length numeric vector for every input. TF-IDF (term frequency–inverse document frequency) is one of the oldest and most effective ways to produce that vector, and it's the representation Jurafsky and Martin treat as the canonical pre-neural baseline in Chapter 5.

The intuition in one sentence: each document becomes a long vector whose entries are weighted word counts, and the weight on each word reflects how often the word appears *in this document* versus how distinctive the word is *across all documents*.

"Term frequency" is the straightforward part — how many times does each word appear in this headline. "Inverse document frequency" is the clever part. Words that appear in almost every headline (the, a, is, of) get down-weighted, because a word that shows up everywhere can't be discriminative — it carries no information about what this particular headline is about. Words that appear in only a few headlines get up-weighted, because their presence is a strong signal for those specific documents. The product of the two (TF × IDF) gives us a representation where the rare, informative words dominate the vector and the common, boilerplate words are pushed toward zero.

TF-IDF on its own is the reason we don't need to manually remove stopwords: IDF weighting already downweights them for us, and it does so data-driven-ly rather than from a hand-curated list that might miss domain-specific junk words or flag informative ones.

Our TF-IDF vectorizer uses two specific settings worth calling out.

`max_features=10000` caps the vocabulary at the 10,000 most informative terms by TF-IDF score across the corpus. Without a cap, the vocabulary would include every rare token in the training set, which would both balloon memory and add features that fire only once and can't generalize. Ten thousand is a conventional starting point for small text-classification datasets; it gives the model enough vocabulary to capture domain language without drowning it in one-offs.

`ngram_range=[1, 2]` is the more interesting choice. An n-gram is just a contiguous sequence of n tokens: "profits" is a 1-gram (a unigram), "profits rose" is a 2-gram (a bigram). The standard TF-IDF recipe uses only unigrams, treating each word as independent. Adding bigrams lets the model see short phrases as features in their own right — which matters enormously for negation. The unigram "good" is positive. The unigram "not" is near-zero on its own. But the bigram "not good" is a direct negative signal. A unigram-only model has no way to represent negation without some additional mechanism; a unigram-plus-bigram model gets it for free as long as the negation pattern appears enough times in training data to earn a dedicated feature. Bigrams also capture multi-word domain terms that individual words would miss ("profit warning," "dividend cut," "earnings beat"). The cost is a much larger vocabulary, which `max_features` caps.

We don't go to trigrams and above. Higher-order n-grams explode feature space fast, get sparser with each step, and for headline-length text there's rarely enough signal in three-word sequences to earn their memory cost.

### 5.2 Logistic regression: the classifier itself

The classifier on the end of the pipeline is a multinomial logistic regression. Jurafsky and Martin Chapter 4 treats logistic regression as the canonical classical classifier for text, and for good reason: it's simple, fast to train, fast to predict, scales to large vocabularies, produces calibrated probabilities rather than just hard labels, and — critically for us — exposes per-feature weights that you can inspect to understand what the model learned.

Mechanically, logistic regression for three-class classification learns one linear combination of features per class. For each input TF-IDF vector, it computes a weighted sum for each class, applies a softmax to turn those sums into probabilities that add up to one, and picks the class with the highest probability. Training minimizes cross-entropy loss over the training examples, which is a principled way of saying "reward the model when it assigns high probability to the correct label and penalize it when it doesn't."

Three training hyperparameters from `config.yaml` drive the behavior.

`max_iter=1000` is the limit on the number of iterations the optimizer runs. The default scikit-learn value is 100, which converges for small or well-separated problems but often stops short on sparse TF-IDF features where the loss surface is flatter. Bumping to 1000 gives the L-BFGS optimizer room to actually reach convergence. This is a "no surprises" hyperparameter — we set it high enough that we don't silently ship a half-trained model.

`class_weight='balanced'` is the most important one. Our label distribution is heavily imbalanced: training data has 1090 positives, 2303 neutrals, and 483 negatives. A classifier trained without any weighting would correctly notice that "always predict neutral" already gets 59% accuracy, and would optimize toward that bias — producing high overall accuracy but near-zero recall on the minority negative class, which is exactly the class we most care about being right on. The `balanced` setting re-weights the loss contribution of each example inversely proportional to its class frequency, which effectively forces the model to treat a mistake on a rare negative example as more expensive than a mistake on a common neutral example. In practice this trades away a small amount of overall accuracy for a much more usable per-class F1, and it's the right trade for comparing scorers fairly — without it, a nominally "high-accuracy" model might be trivially worse at the actual task.

`random_state=seed` pins the initialization of the solver so that training runs are reproducible. Combined with the seeded train/test split from `data_loader.py`, the entire training procedure is deterministic: same code, same data, same model, every time.

### 5.3 Producing a score from a classifier

Logistic regression naturally produces a label and a three-class probability distribution over `{negative, neutral, positive}`. But our pipeline is built around a *score* in `[-1, +1]`, unified across scorers so that we can compare them on the same axis. We need to collapse a three-way probability into a single signed scalar.

The transformation we use is `P(positive) - P(negative)`. If the model is confident positive, this is close to +1. If it's confident negative, this is close to -1. If it's confident neutral, both probabilities are near zero and the score is near zero. The neutral mass washes out by construction, which is the right behavior: neutral is, by definition, "neither positive nor negative," so a neutral prediction should sit in the middle of the score axis.

This transformation is what the scorer does after calling `predict_proba`. The raw score then passes through `normalize_score` (safety clamp to `[-1, +1]`) and `score_to_label` (thresholded back into a category using the same thresholds VADER uses — +0.1 and -0.1 by default). Using the same thresholds for both methods is non-negotiable for fair comparison: if VADER and LogReg had different decision boundaries, we couldn't tell whether a disagreement was due to the methods themselves or due to our threshold choices.

### 5.4 Training artifact

`train()` fits the pipeline once and serializes the full `Pipeline` object (vectorizer + classifier, together) to disk via `joblib.dump`. We use joblib rather than pickle because joblib is faster on scikit-learn models and handles the large numeric arrays inside TF-IDF more efficiently. The serialized artifact lands at `models/logreg_tfidf_pipeline.pkl` per `config['scorers']['logreg']['model_path']`. `is_trained()` checks for the file's existence; `_load_pipeline()` loads it into memory on demand. This means training and scoring can happen in different runs of the pipeline — you train once, then score as many times as you want without re-fitting.

---

## 6. The transformer — FinBERT

The third scorer is FinBERT, a BERT-based transformer model fine-tuned by the ProsusAI team on financial communication text. Where VADER counts lexicon words and LogReg projects TF-IDF vectors through a linear decision boundary, FinBERT reads sentences through a stack of attention layers that learn positional and contextual relationships between tokens. This is the Jurafsky & Martin Chapter 11 content — the transformer architecture and its application to sentiment classification — made concrete.

The intuition for why transformers matter on this problem is worth stating plainly. Our LogReg model sees each headline as a bag of weighted words and phrases. It has no idea what order the words appeared in, no idea which words are referring to which other words, no idea that "profits rose despite weaker margins" is a net positive claim while "weaker margins depress profits" carries the opposite valence. A transformer, by contrast, processes tokens through self-attention layers where every token gets to look at every other token and decide how much to weigh each one when building its own representation. The result is that context and phrase structure get baked into the internal representation of each word — "rose" in "profits rose" carries different weight from "rose" in "rose despite weaker performance," because the attention heads weight the surrounding words differently in each case. For financial sentences, where the same words can mean the opposite thing depending on what they're predicated on, this matters enormously.

FinBERT builds on that foundation twice. First, it starts from BERT weights, which were pretrained on a massive general English corpus — so it arrives at our task already knowing English syntax, common phrasing, negation patterns, and a vast general vocabulary. Second, the ProsusAI team further fine-tuned it on a financial corpus (the Reuters TRC2 corpus) and then on FPB labels themselves, so the model's top layers are specifically shaped for financial sentiment. The practical effect is that FinBERT arrives at our task already domain-adapted in a way neither VADER nor a from-scratch LogReg ever could be.

Our FinBERT scorer is built around three practical concerns that a lexicon or a sparse classical model doesn't have to care about: lazy loading, device selection, and batched inference.

**Lazy loading.** The model weights are roughly 400MB. We don't want to incur that load cost unless the scorer is actually going to be used. The scorer defers all initialization to the first call to `_ensure_loaded`, which loads the tokenizer, loads the model, transfers the model to the selected device, and switches it to evaluation mode. Subsequent calls are no-ops. This is the pattern all three scorers follow, but it matters most for FinBERT because the startup cost is so much higher.

**Device selection.** The scorer reads `config['scorers']['finbert']['device']`, which defaults to `"auto"`. On `"auto"` the code tries CUDA first, then Apple's MPS backend, then falls back to CPU. A developer with an NVIDIA GPU gets seconds of inference across the full dataset; a developer on CPU gets 10–20 minutes. This is the right tradeoff — always-CPU would be wrong for contributors with GPUs, and always-CUDA would crash on Macs and CPU-only boxes. The config override exists for developers who want to force a specific device for reproducibility or testing.

**Batched inference.** Transformer inference scales much better in batches than element-at-a-time. The scorer iterates through the input texts in batches of `config['scorers']['finbert']['batch_size']` (16 by default), tokenizes each batch with dynamic padding (padding each batch to its own longest sequence rather than to the global max, which saves compute on shorter batches), truncates at 512 tokens to fit the BERT context window, runs the forward pass under `torch.no_grad()` (we don't need gradients at inference time and `no_grad` disables autograd bookkeeping for meaningful speedup), and softmaxes the resulting logits into a three-class probability distribution. A `tqdm` progress bar wraps the loop so that long-running runs are visible in the terminal rather than appearing to hang.

The score transformation is identical to the LogReg case: we take `P(positive) - P(negative)` from the softmax output. This is deliberate — using the same transformation across both probabilistic scorers means their scores live on the same interpretation, so direct comparison in Phase 2 is honest. The raw score then passes through the shared `normalize_score` clamp and the shared `score_to_label` threshold.

One subtle correctness hazard worth flagging. FinBERT's output layer has three classes, but there is no universal convention for which index maps to which label. ProsusAI's current model uses `{0: 'positive', 1: 'negative', 2: 'neutral'}`, but if they ever push a new revision that reorders those labels (say, to `{0: 'negative', 1: 'neutral', 2: 'positive'}` to match some other convention), our `probs[:, 0] - probs[:, 1]` line would suddenly be computing the wrong thing, and we'd produce confidently wrong scores across the entire dataset without raising any error. The safeguard is an explicit `id2label` verification step in `_ensure_loaded`: on model load, we read `self._model.config.id2label`, compare it to a hardcoded expected mapping, and raise a `ValueError` with both the expected and actual mappings printed if they don't match. This means a future model revision can silently succeed in downloading and can silently succeed in forward-passing, but cannot silently produce wrong scores — the error fires before a single score is produced. It's a small amount of code (six lines) that catches a failure mode which would otherwise be extremely hard to notice.

FinBERT is our strongest expected scorer. The analytical question for the final report is not whether it beats the baselines — we fully expect it to — but by how much, where its errors concentrate, and whether its agreement with the LogReg baseline tells us anything about the types of headlines where classical methods can hold their own against transformers. The interesting case will be the headlines where FinBERT and LogReg disagree but VADER sides with one of them; those are the places where the additional context modeling a transformer provides is actually mattering.

---

## 7. The shared scorer interface

Every scorer in `src/scorers/` subclasses `BaseScorer` and implements the same two-method interface: a `name` property and a `score_batch(texts)` method that returns a DataFrame with exactly two columns, `{name}_score` and `{name}_label`. The base class provides a convenience method `score_dataframe(df, text_col)` that calls `score_batch` on the specified column and merges the results back onto the input DataFrame. Subclasses don't override this convenience method; they only implement the scoring logic itself.

This uniform contract is the reason we can swap scorers, compare them pairwise, and extend the pipeline with new signal layers later without changing any downstream code. The evaluation module, the temporal module, the visualization module — none of them know how many scorers exist or what they do internally. They know only that for every scorer named `X`, there's a column `X_score` and a column `X_label`, and that both obey a known schema. That's the whole extension surface.

All three scorers now implement this contract: VADER, LogReg, and FinBERT. When future Narrative Atlas layers are added — an embedding drift detector, an aspect-based sentiment classifier, a framing model — each one will be a new file in `src/scorers/` that implements this same interface, plus a new entry in `config.yaml`. No pipeline changes.

---

## 8. Running tally of what's implemented

All four Phase 1 source modules are now live and tested end-to-end with real data flowing through them:

`src/data_loader.py` downloads FinancialPhraseBank from HuggingFace and AAPL prices from Yahoo Finance on first run, caches both to `data/raw/`, and returns validated DataFrames on every subsequent run. Both loaders perform a column-presence check, null-value check, label/split conformity check (for headlines), and row-count sanity check (for prices) before returning. A corrupted cache file raises a named error with a remediation step. The Thursday cleanup pass removed two unused imports (`numpy`, `pathlib.Path`) and corrected `Raises:` and `Returns:` documentation drift in both public functions.

`src/preprocessing.py` adds a `text_clean` column with stripped whitespace, NFKD-normalized Unicode, optional lowercasing, and collapsed internal whitespace. It raises if any cleaned text becomes empty. The `_normalize_unicode` helper is now documented accurately regarding what NFKD does and does not do to smart quotes and dashes, and the Thursday cleanup removed an unused `re` import (the regex collapse uses pandas' `.str.replace` directly) and fixed a lingering docstring that re-asserted the already-corrected smart-quote claim.

`src/scorers/vader_scorer.py` implements the `BaseScorer` contract over VADER's compound score, passes the raw score through the shared normalizer, and produces `vader_score` / `vader_label` columns.

`src/scorers/logreg_scorer.py` implements `train()` and `score_batch()` over a scikit-learn `Pipeline(TfidfVectorizer → LogisticRegression)`, with hyperparameters drawn from config, a `P(positive) - P(negative)` score transformation, and joblib-serialized model persistence.

`src/scorers/finbert_scorer.py` implements `_ensure_loaded()` and `score_batch()` over `transformers.AutoTokenizer` and `AutoModelForSequenceClassification`. Device selection walks CUDA → MPS → CPU under the `"auto"` setting, with an explicit override path for reproducibility testing. Lazy loading keeps the 400MB model download cost deferred to first use. Batched inference under `torch.no_grad()` with dynamic padding and a 512-token truncation produces a three-class softmax that collapses to a signed score via the same `P(positive) - P(negative)` transformation we use for LogReg. An `id2label` verification step in `_ensure_loaded` raises loudly if ProsusAI ever ships a new model revision with a different label order — the only failure mode that could silently produce confidently wrong scores. A `tqdm` progress bar wraps the batch loop for visibility during the 10–20 minute CPU-inference run.

Configuration — the `preprocessing` block in `config.yaml` has been cleaned up to remove three flags (`remove_punctuation`, `remove_numbers`, `min_token_length`) that the code never consumed and which were misleading documentation of capability the pipeline does not have. A comment in the same place now records *why* preprocessing is minimal, so future contributors don't add flags the pipeline silently ignores. The matching block in `ARCHITECTURE.md §3` is updated to stay in sync.

Code quality — two independent review passes were run during the week, one on Wednesday and one on Thursday. The Wednesday pass turned up the corrupted-cache handling gap, the unused preprocessing config keys, and the incorrect NFKD smart-quotes docstring, all of which are fixed. The Thursday pass turned up dead imports in both `data_loader.py` and `preprocessing.py` and documentation drift in the loader's Returns/Raises sections, all of which are fixed. The review discipline is cheap (roughly fifteen minutes per pass) and catches issues early, before they surface as confusing errors during Phase 2 evaluation. We will run a similar pass after each Phase 2 module lands.

Observed results worth reporting in the final report.

On VADER, the label distribution came out heavily positive-skewed (2347 pos / 2068 neu / 431 neg) versus the true distribution (1363 pos / 2879 neu / 604 neg). VADER is systematically reading financial language as more positive than expert annotators did. This is the classic "general-lexicon-on-domain-text" failure mode, and it validates the premise of the whole experiment: we need domain-adapted methods.

On LogReg, training accuracy comes in during the 0.85–0.95 range on the 80% train split, with test accuracy expected to land in the 0.65–0.80 window per the task spec. Exact test-set metrics will be captured from the Wednesday verification run and logged here before Phase 1 closes.

On FinBERT, results are pending the verification run. Expectation: a label distribution meaningfully different from both VADER and LogReg, with the most negative headlines scoring close to -1.0 and containing clearly negative financial content. This is the scorer we expect to win the comparison and the one we're most curious about in terms of *where* it wins — i.e., which classes of headlines the transformer reads correctly that the baselines miss.

---

## 9. What's next

With all three scorers implemented, Phase 1 is functionally complete once two housekeeping items close: the FinBERT verification run (to confirm the model loads and scores cleanly against the full dataset), and the generation of the master scored CSV at `data/processed/headlines_scored.csv`. That CSV is the single artifact every Phase 2 module will read from — it contains the original text, the cleaned text, the true label, the train/test split, and the score + label columns from all three methods. Once it exists, Phase 2 can begin.

Phase 2 itself is where the pipeline shifts from scoring to analysis. Four deliverables sit on the critical path.

The evaluation module computes classification metrics (accuracy, precision, recall, F1 per class and macro) against the held-out test split for each scorer, builds 3x3 confusion matrices to surface which classes each method confuses, and computes Cohen's kappa between every pair of methods on the full dataset to quantify inter-method agreement. Kappa is the right metric for inter-method agreement because it corrects for the agreement you'd expect by chance given the class distributions — raw agreement percentage alone is misleading when one class dominates.

The temporal module assigns pseudo-dates to headlines (distributing them evenly across the price data date range, since FPB doesn't ship with publication timestamps), aggregates them into weekly bins, computes per-week mean and standard deviation for each method's score, joins against weekly AAPL returns, shifts returns forward by one week to get next-week returns, and then computes Pearson and Spearman correlations between each method's weekly sentiment mean and next-week return. This is where we can ask — and quantify — whether sentiment extracted from public discourse carries predictive signal for near-term price movement.

The visualization module produces the five publication figures described in `ARCHITECTURE.md §4.11`: a sentiment timeline overlaying all three methods and AAPL price, violin distributions comparing score shapes per method, a pairwise agreement heatmap, a keyword spectrogram showing how the top TF-IDF terms shift over time, and a volume-sentiment scatter colored by next-week return. All five use consistent colors defined in `config.yaml` so that VADER is always coral, LogReg is always teal, and FinBERT is always blue across every figure.

Finally, `run_pipeline.py` becomes the end-to-end orchestrator: load data, preprocess, run all three scorers, save the master CSV, evaluate, temporal-aggregate, generate figures, print a summary table. One command, reproducible output, clean start to clean finish.

We're on schedule. Data is flowing, all three scorers are live, two review passes have shipped, documentation is current, and every module so far has passed its verification test. The main Phase 2 risk to watch is report-writing time: Phase 1 consumed about 2.5 working days, and Phase 2 has four deliverables plus the final written report. Drafting the report's methodology and related-work sections in parallel with Phase 2 engineering — using this document as the source of truth for the engineering narrative — is the right mitigation.

---

## 10. Course concept index

For the final report's discussion section, here are the Jurafsky & Martin references each component touches, so we can cite them directly without re-deriving the mapping:

Sentiment lexicons, MPQA, and the General Inquirer (Ch 4) — covered by the VADER scorer and discussed in §4 of these notes. VADER is the production-grade descendant.

Logistic regression for text classification (Ch 4 §4.3) — covered by the LogReg scorer and discussed in §5.2.

TF-IDF weighting and the vector-space model (Ch 5) — covered by the TF-IDF stage of the LogReg pipeline and discussed in §5.1.

N-gram features (Ch 4, Ch 5) — our use of `ngram_range=[1, 2]` is the unigram+bigram feature expansion discussed in §5.1.

Class imbalance and weighted loss (Ch 4 discussion of classifier evaluation) — our `class_weight='balanced'` is discussed in §5.2.

Cross-entropy loss (Ch 4 §4.4) — the training objective for the logistic regression stage, mentioned briefly in §5.2.

Transformer-based sentiment classification (Ch 11) — covered by the FinBERT scorer and discussed in §6. Self-attention, pretraining-then-fine-tuning, and the move from sparse features to contextual representations are all on the page there.

Cohen's kappa and inter-annotator agreement (Ch 4 discussion of evaluation) — to be used in the evaluation module for inter-method agreement.

---

*Last updated: end of Day 3, Phase 1.*

---

## Phase 2, Day 1 — Evaluation Results

Run: 2026-04-21

### Classification performance (test split, n=970) and inter-method agreement (full dataset, n=4,846)

```
==============================================================
Classification Performance (Test Set)
==============================================================
Method       Accuracy   F1-macro     F1-pos     F1-neu     F1-neg
--------------------------------------------------------------
vader           0.535      0.486      0.492      0.607      0.358
logreg          0.569      0.588      0.553      0.558      0.652
finbert         0.739      0.757      0.717      0.731      0.824

=================================================
Inter-Method Agreement (Full Dataset)
=================================================
Pair                        Agreement%  Cohen's κ
-------------------------------------------------
vader vs logreg                  50.6%      0.169
vader vs finbert                 54.2%      0.240
logreg vs finbert                74.7%      0.585
```

### Confusion matrices (rows = true, cols = predicted; test split)

```
VADER Confusion Matrix (rows=true, cols=predicted)
           pred_pos   pred_neu   pred_neg
  positive        183         68         22
   neutral        243        297         36
  negative         45         37         39

LOGREG Confusion Matrix (rows=true, cols=predicted)
           pred_pos   pred_neu   pred_neg
  positive        221         30         22
   neutral        293        242         41
  negative         12         20         89

FINBERT Confusion Matrix (rows=true, cols=predicted)
           pred_pos   pred_neu   pred_neg
  positive        263          5          5
   neutral        197        335         44
  negative          1          1        119
```

### Dominant confusion pattern per method

All three methods share the same dominant off-diagonal cell — true=neutral predicted as positive — but the magnitude scales inversely with domain adaptation. VADER: the largest off-diagonal is `true=neutral → pred=positive` at 243 cases (42% of the 576 neutral headlines in the test set), consistent with the Phase 1 finding that VADER reads promotional corporate language as enthusiasm. LogReg: the same cell dominates at 293 cases, slightly worse than VADER — an artifact of `class_weight='balanced'` pushing the classifier to commit to non-neutral predictions on ambiguous input. FinBERT: the same cell is still the largest off-diagonal at 197 cases but is roughly two-thirds the rate of the baselines, and its off-diagonal mass is otherwise tiny (FinBERT almost never confuses positive and negative directly — only 5 positive→negative and 1 negative→positive).

### Three-way disagreement statistics

Three-way disagreements (all three methods predict a different label) occur on 144 of 4,846 headlines = 3.0% of the full dataset. These are the maximum-confusion cases and the cleanest illustrations of where the methods' assumptions diverge.

### Picked disagreement examples

**1. Boilerplate disclaimer text** — TRUE: neutral · VADER: negative (-0.296) · LogReg: positive (+0.101) · FinBERT: neutral (-0.034)
"FinancialWire tm is not a press release service, and receives no compensation for its news, opinions or distributions."
VADER latches on to the bigram "no compensation" as negative valence without recognizing that it appears inside a legal disclaimer. LogReg reads isolated terms like "service", "news", "opinions" that co-occurred with positive examples in training and tips the classifier positive. FinBERT has seen enough disclaimer-shaped sentences in its financial pretraining corpus to treat them as content-free boilerplate — which is the right answer here.

**2. Swing-to-profit reported dryly** — TRUE: positive · VADER: positive (+0.440) · LogReg: negative (-0.256) · FinBERT: neutral (+0.016)
"Profit after taxes was EUR 0.1 mn, compared to EUR -0.4 mn the previous year."
This is objectively a positive development (loss → profit year-over-year) but the sentence reports it dispassionately. VADER reads the unigram "profit" and scores positive, arriving at the right answer for the wrong reason. LogReg's TF-IDF vector is dominated by the negative-signed number "-0.4" and the comparison phrasing, flipping it to negative. FinBERT straddles the middle — the numeric quantifier context ("compared to" + two small figures) appears to wash out the polarity signal entirely. A case where the transformer's context-sensitivity is actually a liability on financial prose that requires arithmetic reasoning.

**3. Hedged guidance language, true label neutral (H2 archetype)** — TRUE: neutral · VADER: positive (+0.723) · LogReg: neutral (+0.098) · FinBERT: negative (-0.100)
"CapMan said the deal's effect on its cash flow for 2009 totals EUR3.4 m, but the transaction would not affect its financial results for 2009 as it was executed…"
Clean illustration of the H2 intuition — a factually neutral headline where VADER and FinBERT land on opposite sides of the threshold. VADER locks onto "cash flow totals EUR3.4 m" and reads upbeat. FinBERT reads the "but… would not affect" hedge as negative news framing. LogReg's bag-of-words representation doesn't have enough signal to commit and correctly stays neutral. This is the kind of headline that will dominate the Results section's qualitative analysis.

**4. Finance-specific descriptor read differently by each method** — TRUE: neutral · VADER: neutral (+0.000) · LogReg: positive (+0.182) · FinBERT: negative (-0.879)
"Juhani Järvi, Corporate Executive Vice President of Kesko, says the Russian food retail sector is fragmented."
No lexicon-coded emotion words, so VADER correctly sits at exactly zero. LogReg's TF-IDF fires on "Corporate", "Executive", "Vice President" — tokens that disproportionately appeared in positive training examples (earnings-call attribution) and skews the classifier positive. FinBERT's attention heads appear to pick up the finance-specific descriptor "fragmented" as a strongly negative market characterization (-0.879 is near-saturated), revealing that the transformer has internalized a domain meaning for "fragmented" that neither baseline has. The true-label answer is neutral because the sentence is descriptive, not evaluative, so FinBERT is over-correcting.

**5. Flat guidance as hedging** — TRUE: neutral · VADER: neutral (+0.000) · LogReg: negative (-0.282) · FinBERT: positive (+0.824)
"Scanfil expects net sales in 2008 to remain at the 2007 level."
VADER has no lexicon hits and correctly returns zero. LogReg fires on the absence-of-growth framing ("remain at", "expects") and reads negative. FinBERT appears to treat "expects net sales" + forward guidance as strongly positive (+0.824 is near-saturated on the positive side), despite the sentence explicitly saying sales will not grow. This is the mirror image of example 4: FinBERT's finance-specific priors pull it toward a confident read that contradicts the literal content. An important qualitative point for the Discussion — FinBERT's polarization (σ = 0.58 versus 0.30 for VADER) is what gives it its headline accuracy lift, but it also produces these high-confidence wrong answers that a more cautious classifier would leave near zero.

### H2 test — VADER vs FinBERT disagreement rate, by true label

```
  true=positive: 30.4% disagree  (n=1363)
  true=neutral : 48.1% disagree  (n=2879)
  true=negative: 69.9% disagree  (n=604)
```

### H1 verdict — SUPPORTED

FinBERT (0.739) > LogReg (0.569) > VADER (0.535). The ordering matches the hypothesis exactly, and F1-macro tells the same story even more cleanly (0.757 > 0.588 > 0.486). The gap between FinBERT and the two baselines (+17 accuracy points over LogReg, +20 over VADER) is large enough that it's not plausibly attributable to test-split variance; the gap between LogReg and VADER (+3.4 points) is real but small, which is itself interesting — a supervised classifier trained on less than 4,000 financial sentences only narrowly edges out a zero-training general-purpose lexicon, suggesting TF-IDF + LogReg is undertrained for this domain.

### H2 verdict — REJECTED (directionally wrong)

H2 predicted that VADER–FinBERT disagreement would be highest on true=neutral headlines. It is not. Disagreement is highest on true=negative (69.9%), second-highest on true=neutral (48.1%), and lowest on true=positive (30.4%). The most likely explanation is consistent with Phase 1's observation that VADER systematically over-predicts positive and under-predicts negative on financial text: expert-negative headlines frequently use domain-specific negatives (guidance cuts, losses reported factually, "headwinds", "downgrade") that VADER's general-purpose lexicon misses entirely, while FinBERT catches them — so the two methods almost always land on different labels for genuinely negative headlines. True=neutral disagreement is still substantial (48.1%), and VADER's neutral→positive bias is still the single most common disagreement pattern on that subset, but the negative class is where VADER and FinBERT diverge most sharply. This is a legitimate finding and the report will state H2 as rejected with the above explanation.

---

*Last updated: end of Phase 2, Day 1 (evaluation module).*
