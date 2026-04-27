# Layer 2 — HMM validation v0.3

This experiment is a single-block patch to `experiments/layer_2/hmm_validation_v0_2/run.py`. It tests the leading candidate hypothesis surfaced by v0.2's PARTIAL_CONFIRMED outcome: that the missing covariate-slope update in EM accounts for the residual Hamming(T) plateau at the V_prior = 0.01 endpoint of v0.2.

The v0_2 directory is preserved as the immutable record of the V_prior sweep without β_x. v0.3 is a parallel experiment, not a replacement. Each patch tests exactly one hypothesis so that the diagnostic value of each run is preserved.

## What v0.3 changes

`run.py` is copied from `experiments/layer_2/hmm_validation_v0_2/run.py` with one change. After the per-state `nu[k]` Newton updates in `em_one`'s inner EM loop, and before the opportunistic-flag M-step, an additional Newton step is taken for the state-invariant covariate slope `beta_x`:

```python
# M-step: beta_x (state-invariant slope, one Newton step per outer iteration)
grad_beta = 0.0
hess_beta = 0.0
for k in range(K):
    w = gamma[:, k] * A_d
    if w.sum() < 1.0:
        continue
    p = expit(nu[k] + beta_x * x); y = (delta == -1).astype(float)
    grad_beta += w @ ((y - p) * x)
    hess_beta += -(w @ (p * (1-p) * x * x)) - 1e-3
if hess_beta < -1e-9:
    beta_x = beta_x - grad_beta / hess_beta
```

The slope is state-invariant per the §4.1 spec — a single scalar `beta_x` summed over both states with the per-state posterior responsibility `gamma[:, k] * A_d` as the weight. The `if hess_beta < -1e-9` guard handles the rare degenerate-weight case where the Hessian numerator is near zero. The v0.1 calibration patch and the v0.2 V_prior sweep harness are carried forward unchanged. No other line of `run.py` is modified.

## Why v0.3 replays the full V_prior sweep, not an always-T-only diagnostic

The cheapest diagnostic for the "missing β_x" hypothesis is an always-T-only fit at V_prior = 0.01 with the β_x update enabled — roughly 50 seconds single-core. The full v0.2-style sweep with β_x is roughly 720–760 seconds (β_x adds ~15–20% per-fit cost on top of v0.2's 634.5 s). The 11-minute compute differential buys a strictly more informative experiment for three reasons.

First, β_x's effect on the always-C cohort and the switching cohort is informative independently of its effect on always-T. Always-C executives see the same `x` distribution and the same `beta_sell = 0.3`, so the same miscalibration mechanism applies — but the direction of the bias is opposite (high-x C-cohort slices have higher true sell propensity than the harness predicts, which makes them look more "C-like" to a fitted ν_C and helps Hamming(C) rather than hurting it). If Hamming(C) improves substantially under β_x, the miscalibration story is symmetric and complete; if it does not, Hamming(C) is bounded by something else and the next experiment has a different scope.

Second, the v0.2 Hamming(switch) peak at V_prior = 0.1 (0.297, versus 0.241 at V_prior = 0.01) is roughly 2σ on a 60-executive Hamming MC distribution and survives as a structural signal worth distinguishing. Two competing readings sit on it: a bimodal-multistart hypothesis (some EM starts find the strong-anchor mode at V_prior = 0.1 and others find a wrong-basin attractor, with the LL-best winner being neither cleanly), and an emission-overlap hypothesis (at intermediate prior strength the means are pulled partway toward truth but stay close enough to the wrong-basin attractor that within-class variance dominates the between-class signal). β_x is largely orthogonal to both readings — it operates on the action channel, not the narrative channel — so if the V_prior = 0.1 peak survives β_x correction, the orthogonality test rules out the action-channel-attributable explanations and isolates the residual to the narrative-emission overlap or multistart story.

Third, μ-RMSE response to β_x is informative about emission coupling. β_x is in the action emission, not the narrative emission, so first-order it should not move μ-RMSE. But the EM E-step computes posteriors from the joint emission likelihood, so a corrected action-channel likelihood reweights per-slice posteriors and feeds back into the narrative-channel M-step. Whether that feedback is small (clean spec) or large (coupled identification) is unanswerable without the direct comparison.

## Hypothesis under test

If the missing β_x slope update is the second contributing cause to the v0.2 Hamming(T) plateau (the first being the weak default V_prior, which v0.2 already addressed), then fitting `beta_x` should drop Hamming(T) at V_prior = 0.01 from 0.188 (v0.2) toward small values (~0.05–0.10). Hamming(switch) and ECE should drop in lockstep on the switching cohort, since the action-channel mis-fit drives mis-labelling there too. μ-RMSE at V_prior = 0.01 should remain near 0.029 (the prior anchor is unchanged); any movement signals coupled identification through the posterior. Hamming(C) is the wildcard described above.

The β_x diagnostic is also a minimal test of the §4 spec's I6 identifiability condition, which asserts that the covariate-dependent action emission with state-invariant slope is identifiable. A clean Hamming(T) drop is positive evidence for I6 at finite samples in the simplified harness; a plateau is mild concern that flows into the v0.5 design.

## What v0.3 does NOT validate

A clean BETA_X_CONFIRMED outcome here does not validate the §4 specification. The narrative-emission prior (`mu_prior = (0.0, 0.4)`) is still hard-coded at the generator's truth at V_prior = 0.01; that part of the empirical-Bayes tautology is unchanged from v0.2. v0.3 is a diagnostic for action-channel identification, not narrative-channel identification. The actual identification test — narrative `mu_prior` learned from a population rather than placed at truth — is staged for v0.5. v0.3's role on the path is to de-risk v0.5 on the action-channel side: if β_x cannot recover label assignment even when the narrative prior is dominant and centred on truth, hierarchical pooling alone will not save v0.5.

## Single-command reproduction

```
cd experiments/layer_2/hmm_validation_v0_3
pip install -r requirements.txt
python run.py --seed 20260426
```

Expected wall-clock: roughly 11–13 minutes single-core (5 V_prior values × 3 cohorts × 60 executives × 10 multistarts ≈ 9000 EM fits, with β_x adding ~15–20% per-fit cost over v0.2's 634.5 s).

## Files in this directory

`run.py` is the harness with the v0.1 calibration patch, the v0.2 V_prior sweep harness, and the new β_x M-step. `requirements.txt` is identical to v0.2's. `notes.md` records the diff against v0.2, the hypothesis, the reproducibility command, the v0.2 quantitative-mechanism analysis it builds on, and three empty subsections for outcomes (`BETA_X_CONFIRMED`, `BETA_X_PARTIAL`, `BETA_X_NULL`). `decision_tree.md` is the runbook for the next round of work; it documents what gets updated under each of the three possible outcomes.

`STATUS.md` is intentionally not present until the run has completed and an outcome has been selected. The decision-tree branch determines which artifacts are updated and in what order.

## Relationship to upstream documents

The Layer 2 design document is **not** modified by the staging of v0.3. The research document at `docs/layers/layer_2/research/Insider Divergence Detection as Bayesian HMM Spec with Covariate-Dependent Emission.md` is **not** modified by the staging of v0.3. Both are read-only inputs.

The §4.3.6 follow-up note at `docs/layers/layer_2/research/EXPECTED_VALUES_FOLLOWUP.md` is updated separately to record v0.2's internal-inconsistency observation: the (μ-RMSE ≈ 0.10, Hamming(T) ≈ 0.05) joint values do not co-occur at any V_prior in the actual harness, which is stronger evidence than two seeded runs disagreeing.

## Diagnostic companion

`diagnose.py` is the inline diagnostic recommended by the v0.3 BETA_X_NULL outcome's `STATUS.md`. It re-runs the v0.3 default cell at `V_prior = 0.01` only (3 cohorts × 60 executives × 10 multistarts, ~150 s wall-clock) and writes per-executive identifiability data to `outputs/diag.json` that `run_vprior_sweep` aggregates away. Three failure-mode tests motivate the per-executive granularity. First, the **label-fixing-swap** reading: `diagnose.py` records the `label_swaps` count from each executive's `diag` dict, so the per-cohort swap rate at the strongest prior anchor is directly readable; if always-T executives show swap rates above ~10–15%, the post-hoc `mu[0] > mu[1]` reorder is fighting the prior anchor and is the proximate cause of the Hamming(T) plateau. Second, the **transition-matrix-identification** reading: the script records the converged `log_A` per executive, which on always-T executives should be dominated by the Dirichlet prior `alpha_A = (50.0, 5.0)` and produce rows near `(0.91, 0.09)` regardless of the truth (always-T executives have no observed C → T transitions to learn from). If always-T `log_A` rows drift materially from the prior anchor, the Dirichlet prior is being overwhelmed by a small number of likelihood-driven label flips per trace, which is itself a label-recovery signal. Third, the **per-executive Hamming distribution** reading: the script's console summary reports the min, q1, median, mean, q3, max of per-executive Hamming on each cohort, distinguishing a unimodal-ambiguous failure mode (the cohort-folding `min(h0, h1)` metric reflects irreducible per-slice emission overlap, with per-executive Hamming clustered near the cohort mean) from a bimodal-orientation-flipped mode (some executives near 0, others near 0.5, with the mean reflecting the population mixture rather than per-executive uncertainty). The per-executive `mu_T`, `mu_C`, and `beta_x` records also let us check directly whether `beta_x` is converging to a non-zero value (testing the "β_x is fitted but its discriminating power is too small to matter" reading from the v0.3 BETA_X_NULL analysis).
