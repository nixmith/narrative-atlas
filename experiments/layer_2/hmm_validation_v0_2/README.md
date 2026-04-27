# Layer 2 — HMM validation v0.2

This experiment is a `V_prior`-only sweep at the default cell of the v0.1 grid (β_sell = 0.3, a_chan = 0.6). It tests one hypothesis flagged in `experiments/layer_2/hmm_validation_v0_1/STATUS.md`: that the v0/v0.1 threshold-failure pattern (μ-RMSE high, posterior entropy low, multi-start agreement high — the *structural-identification fingerprint*) reflects EM converging to a wrong local maximum that the default `V_prior = 4.0` Normal prior on `mu` is too weak to pull EM out of.

The v0_1 directory is preserved as the immutable record of the calibration-patch experiment. v0.2 is a parallel experiment, not a replacement. Each patch tests exactly one hypothesis so that the diagnostic value of each run is preserved.

## What v0.2 changes

`run.py` is copied from `experiments/layer_2/hmm_validation_v0_1/run.py` with two changes confined to the validation harness. The model code (`gen_executive`, `log_emissions`, `forward_backward`, `em_one`) is byte-identical to v0.1.

The first change is a confirmation: `em_one` already exposes `V_prior` as a keyword argument with default `4.0`, and that default is left untouched. v0.2 simply exercises that knob from the harness.

The second change replaces the `(beta_sell, a_chan)` grid sweep with a `V_prior`-only sweep at the default cell. The function `run_vprior_sweep` runs the same per-cohort metrics machinery used in v0.1 — sample 60 executives per cohort with `T` drawn from `lognormal(log(38), 0.7)` clipped to `[10, 200]`, fit `em_one` with the harness's `V_prior` set to one of `(0.01, 0.1, 1.0, 4.0, 64.0)`, record per-cohort Hamming, μ-RMSE, multi-start fraction, mean posterior entropy, and (for the switching cohort) ECE. The default value `V_prior = 4.0` corresponds to the v0.1 setting and serves as the on-grid control.

`main()` writes `outputs/results.md` as a small markdown table with rows = `V_prior` and columns = Hamming(switch), Hamming(T), Hamming(C), ECE, μ-RMSE, multistart, entropy. `outputs/results.json` contains the raw list-of-dicts (per-cohort metrics for each `V_prior` value).

The v0.1 calibration patch (the `np.log(0.4 / 0.6)` / `np.log(0.2 / 0.8)` change to `log_emissions`) is carried into v0.2 unchanged. No other model logic is modified.

## Hypothesis under test

If EM under the v0.1 harness is finding a wrong local maximum that the (unbiased but weak) default `V_prior = 4.0` Normal prior cannot pull out of, then anchoring the prior more strongly should drop μ-RMSE toward zero and Hamming toward small values, while the convergence diagnostics drift only slightly. Concretely, we expect:

- **μ-RMSE** falls monotonically as `V_prior` decreases from 64 → 0.01, approaching ~0.02 at the strongest setting (because the prior mean *is* the truth, so the prior-dominated posterior centres on truth by construction).
- **Hamming** on each cohort falls in lockstep with μ-RMSE, because the labelling step depends on which Gaussian assigns higher likelihood to each slice, and that depends on `mu` recovery.
- **multi-start fraction** drifts only slightly. A strong prior reduces the basin-of-attraction problem (all starts get pulled toward the same anchor), so this metric should rise modestly or stay flat.
- **posterior entropy** drifts only slightly, since the latent-state posterior is governed by emissions/transitions more than by the prior on `mu`.

## What a positive result confirms — and what it does NOT confirm

A positive result here (μ-RMSE drops to near zero as `V_prior` shrinks) confirms the *structural-identification hypothesis*: that the v0/v0.1 failure pattern was not an optimization failure and not a calibration failure, but EM converging to a wrong local maximum that a stronger prior anchor pulls it out of.

A positive result here does **not validate the §4.1 specification**. The v0.2 design lets the prior anchor `mu` to the generator's true means by construction (`mu_prior = (0.0, 0.4)`, exactly the generator's `mu_T = 0.0`, `mu_C = 0.4`). When `V_prior` is small the prior dominates the data; when the prior mean is the truth, the posterior mean is also the truth. This is a tautology of empirical Bayes, not evidence about the data.

The actual identification test — whether the §4 spec recovers `mu` from data when the prior mean is *not* placed at the generator's truth — is staged for v0.5, which expands the harness to (a) hierarchical Type-II ML pooling so the prior mean is *learned* from a population rather than hard-coded, (b) a covariate-slope EM update for `beta_x`, and (c) a 2-channel narrative emission. v0.2 is a strict prerequisite check: if a strongly anchored prior cannot recover `mu` even when its mean *is* truth, no amount of hierarchical pooling will help. v0.2 establishes the lower-bound identification target that v0.5 must approach.

## Single-command reproduction

```
cd experiments/layer_2/hmm_validation_v0_2
pip install -r requirements.txt
python run.py --seed 20260426
```

The harness writes `outputs/results.json` (raw list-of-dicts) and `outputs/results.md` (the `V_prior` × metrics table). Wall-clock cost is approximately 5/9 of the v0.1 cost — five `V_prior` values × three cohorts × 60 executives ≈ 900 EM fits versus v0.1's nine cells × three cohorts × 60 ≈ 1620 — so expect roughly 11–12 minutes single-core if v0.1 ran in 20–21 minutes.

## Files in this directory

`run.py` is the harness with the v0.1 calibration patch carried forward and the validation harness replaced by `run_vprior_sweep`. `requirements.txt` is identical to v0.1's. `notes.md` records the diff against v0.1, the hypothesis, the reproducibility command, and three empty subsections (`Outcome: STRUCTURAL_CONFIRMED`, `Outcome: PARTIAL_CONFIRMED`, `Outcome: ANOMALOUS`) that will be populated after the run completes. `decision_tree.md` is the runbook for the next round of work; it documents what gets updated under each of the three possible outcomes.

`STATUS.md` is intentionally not present until the run has completed and an outcome has been selected. The decision-tree branch determines which artifacts are updated and in what order.

## Relationship to upstream documents

The Layer 2 design document is **not** modified by the staging of v0.2. The research document at `docs/layers/layer_2/research/Insider Divergence Detection as Bayesian HMM Spec with Covariate-Dependent Emission.md` is **not** modified by the staging of v0.2. Both are read-only inputs to this experiment; only the *outcome* of running v0.2 (per `decision_tree.md`) can authorize downstream document changes, and even then design-document edits are deferred until the v0.5 actual identification test resolves.
