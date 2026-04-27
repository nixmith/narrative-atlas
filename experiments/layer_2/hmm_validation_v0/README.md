# Layer 2 — HMM validation v0

This experiment is the synthetic-data validation harness for the Layer 2 hierarchical Bayesian HMM. It is the v0 harness: a tractable approximation of the §4 specification committed in `docs/layers/layer_2/Layer2_Insider_Divergence.md`. It validates that the *family* of HMMs the specification belongs to is identifiable and recoverable on synthetic data drawn from a known generating process. It does not yet validate the specifically committed model; the gaps between this harness and the formal specification are catalogued in `audit.md`.

The harness implements a two-state HMM with one Gaussian narrative emission, a Bernoulli action-direction emission, a Bernoulli opportunistic-flag emission, and an informative-absence factor on the action channel. EM with K=10 multi-start initialization fits per-executive parameters; cohort-aggregated metrics on Hamming rate, Expected Calibration Error, parameter recovery, and multi-start agreement are evaluated against the threshold table in §4.3.3 of the research document.

## Single-command reproduction

```
cd experiments/layer_2/hmm_validation_v0
pip install -r requirements.txt
python run.py --seed 20260426
```

The harness writes three files to `outputs/`: `results.json` (full sweep grid plus pass/fail dictionary), `results.md` (human-readable summary), and `diagnostics.jsonl` (per-executive identifiability diagnostics). `outputs/` is gitignored.

## Interpretation

The harness reports pass/fail at the default sweep point ($\beta_{\text{sell}} = 0.3$, channel-availability $a^{(c)} = 0.6$). The threshold table in `results.md` is the authoritative pass/fail summary; deviations from the expected values in §4.3.6 of the research document are noted in `notes.md`. Robustness sweeps at $\beta_{\text{sell}} \in \{0.0, 0.6\}$ and $a^{(c)} \in \{0.3, 1.0\}$ exercise the harness under stronger mechanical correlation and sparser channel coverage; the corresponding numbers are in the full sweep grid in `results.json`.

## Files in this directory

`run.py` is the harness, extracted from §4.3.4 of the research document. `requirements.txt` declares `numpy` and `scipy` only; no other libraries are imported. `notes.md` records observations from the actual run, any minimal fixes required to get the harness running, and any deltas between produced and expected numbers. `audit.md` enumerates the gaps between the executed harness and the formal §4.1 specification. `STATUS.md` is the entry point for reviewing this experiment — it summarizes the run outcome and points to the other documents.

## Relationship to the design document

Layer 2 v0.2 §11 cites this harness as the primary validation step. A v1 harness — `experiments/layer_2/hmm_validation_v1/` — will be created when the work to expand the harness toward full §4.1 coverage begins. Until v1 exists, the design document does not claim that the full specification has been empirically validated; it claims only that the family containing the specification is identifiable on synthetic data, and the limitations subsection in §11 says so explicitly.
