# Layer 2 — HMM validation v0.4

This experiment is a **counterfactual diagnostic**, not a candidate production model. It is a single-block deletion patch to `experiments/layer_2/hmm_validation_v0_3/run.py` that freezes the EM transition matrix at the canonical generator values `[[0.95, 0.05], [0.20, 0.80]]` throughout EM. Production cannot do this — the spec's hierarchical multinomial-logit transition kernel is the production mechanism, and in production the truth is unknown — so the v0.4 harness is purely a diagnostic to test whether the v0.3 BETA_X_NULL outcome's residual Hamming(T) plateau is driven by the EM's inability to identify the transition matrix on always-T data.

The v0_3 directory is preserved as the immutable record of the V_prior sweep with β_x and the EM-fitted Dirichlet-anchored transition matrix. v0.4 is a parallel experiment, not a replacement. Each patch tests exactly one hypothesis so that the diagnostic value of each run is preserved.

## Trigger from v0.3 BETA_X_NULL STATUS.md

The v0.3 run produced Δ Hamming(T) at V_prior = 0.01 of +0.002 (BETA_X_NULL) and the diagnose.py companion at V_prior = 0.01 surfaced four readings of the strong null. Reading (4) — the **Dirichlet C-row asymmetric anchor** — is what v0.4 tests. The relevant numbers from `experiments/layer_2/hmm_validation_v0_3/STATUS.md`:

The fitted `log_A` on always-T executives at V_prior = 0.01 is essentially the Dirichlet prior `alpha_A = (50.0, 5.0)`: row T→ ≈ (0.921, 0.079), row C→ ≈ (0.102, 0.898), each within 0.013 of the prior anchor. This happens because always-T traces have no observed C→T or C→C transitions to learn from, so the Dirichlet pseudocounts dominate the M-step. The Dirichlet's C-row equilibrium is `(5/55, 50/55) = (0.091, 0.909)` — but the generator's truth on the C-row is `(P_C_to_T, 1 − P_C_to_T) = (0.20, 0.80)`. The Dirichlet prior makes the C-row stickier than truth (P(C | prev=C) = 0.909 vs truth 0.80, P(T | prev=C) = 0.091 vs truth 0.20). When forward-backward smoothing on an always-T executive uses this transition matrix, a phantom-C excursion at slice `t` driven by ambiguous emissions is harder to escape at slice `t+1` than truth would allow. The asymmetry directly inflates Hamming(T).

## What v0.4 changes

`run.py` is copied from `experiments/layer_2/hmm_validation_v0_3/run.py` with one block deletion. The transition-matrix M-step block in `em_one`'s inner EM loop — five lines starting with `n_jk = xi_.sum(axis=0)` and ending with `log_A = np.log(A_new + 1e-9)` — is removed. The `log_A` initialization at the top of the multistart loop (`log_A = np.log(np.array([[0.95, 0.05], [0.20, 0.80]]))`) is preserved unchanged. The transition matrix is therefore frozen at the generator's canonical values throughout every EM iteration of every multistart, regardless of cohort, regardless of V_prior.

The `log_pi` update for the initial state distribution is preserved (initial state is independent of the transition matrix). The β_x M-step from v0.3 is preserved. The narrative-emission M-step, the `nu[k]` and `xi_o[k]` Newton steps, and the V_prior sweep harness are all preserved. No other line of `run.py` is modified.

## Hypothesis under test

If the v0.3 Hamming(T) plateau at 0.190 (cohort mean) and 0.300/0.205/0.080 (T_i-stratified medians at <20, 20–50, ≥50) is driven by the EM's inability to identify the transition matrix on always-T data, **freezing A at the canonical `[[0.95, 0.05], [0.20, 0.80]]` should drop Hamming(T) at V_prior = 0.01 below 0.05** — comfortably under the v0.1 PASS threshold of 0.10 and approaching the per-slice ambiguity floor implied by the four-channel emission overlap.

The alternative: **if Hamming(T) at V_prior = 0.01 stays above 0.10 under frozen-truth-A, the floor is deeper than transition-matrix identification.** Reading (3) from the v0.3 BETA_X_NULL analysis — that short-trace executives carry an inherent identifiability bound under weak forward-backward smoothing regardless of model parameters — becomes the leading candidate, and the v0.5 acceptance band needs to be revised to a length-stratified target.

The intermediate case: Hamming(T) drops materially (>0.10) but plateaus above 0.05. Transition-matrix identification accounts for most but not all of the v0.3 gap, and the residual is per-slice ambiguity on the harder executives.

## What v0.4 does NOT validate

A clean TRANSITION_FLOOR_CONFIRMED outcome here does not validate the §4 specification, and it does not validate the spec's hierarchical multinomial-logit transition kernel. v0.4 freezes A at truth — the production spec learns A from a hierarchical pooling structure where the truth is unknown. The v0.4 result tells us whether *the transition matrix being right* closes the v0.3 gap; it does not tell us whether *the spec's mechanism for getting the transition matrix right* is sufficient. That test is staged for v0.5.

The relationship of v0.4 to v0.5 is: v0.4 establishes whether the transition-matrix axis is load-bearing for v0.5's success. If v0.4 confirms, hierarchical pooling on transitions becomes a necessary v0.5 feature alongside hierarchical pooling on emission means. If v0.4 fails to confirm, v0.5's hierarchical pooling on transitions is not a sufficient cure, and either the v0.5 target needs revision or a deeper structural diagnostic is required first.

## Single-command reproduction

```
cd experiments/layer_2/hmm_validation_v0_4
pip install -r requirements.txt
python run.py --seed 20260426
```

Expected wall-clock: similar to v0.3 (the M-step block deletion saves a tiny amount of compute per outer iteration, but EM convergence may shift slightly because the transition matrix isn't being updated). Estimate 750–800 s single-core.

## Files in this directory

`run.py` is the harness with the v0.1 calibration patch, the v0.2 V_prior sweep, the v0.3 β_x M-step, and the new transition-matrix M-step deletion. `requirements.txt` is identical to v0.3's. `notes.md` records the diff against v0.3, the hypothesis, the reproducibility command, and three empty subsections for outcomes (`TRANSITION_FLOOR_CONFIRMED`, `TRANSITION_FLOOR_PARTIAL`, `TRANSITION_FLOOR_NULL`). `decision_tree.md` is the runbook for the next round of work; it documents what gets updated under each of the three possible outcomes.

`STATUS.md` is intentionally not present until the run has completed and an outcome has been selected. The decision-tree branch determines which artifacts are updated and in what order.

## Relationship to upstream documents

The Layer 2 design document is **not** modified by the staging of v0.4. The research document is **not** modified by the staging of v0.4. Both are read-only inputs.

The §4.3.6 follow-up note at `docs/layers/layer_2/research/EXPECTED_VALUES_FOLLOWUP.md` may be updated by the *outcome* of v0.4 (specifically, if v0.4 produces TRANSITION_FLOOR_CONFIRMED, the cohort-composition-mismatch reading becomes more tractable: §4.3.6's expected Hamming(T) ≈ 0.05 may have been generated under a frozen-truth-A configuration of the harness, which is a fourth possible composition-mismatch hypothesis on top of the long-trace-sample reading from v0.3).
