# Decision tree — `hmm_validation_v0_3`

This file is the runbook for the round of work that follows the v0.3 run. The human runs the patched harness with `python run.py --seed 20260426`, observes the produced numbers in `outputs/results.md`, and selects one of the three branches below. Each branch prescribes the actions Cowork executes once the outcome has been reported and confirmed.

The three branches map directly to the three outcome subsections in `notes.md` (`BETA_X_CONFIRMED`, `BETA_X_PARTIAL`, `BETA_X_NULL`).

## Outcome A: BETA_X_CONFIRMED

Hamming(T) at `V_prior = 0.01` drops to below 0.10 (matching the v0.1 PASS threshold), Hamming(switch) and ECE drop in lockstep on the switching cohort, and μ-RMSE at `V_prior = 0.01` remains near 0.029. The action-channel-attributable component of the v0.2 PARTIAL_CONFIRMED gap is closed; the missing covariate-slope update was the second contributing cause.

This verdict means the path to v0.5 is now de-risked on two fronts. v0.2 confirmed that μ recovers under a sufficiently strong prior anchor (the narrative-channel structural-identification fingerprint), and v0.3 confirms that label recovery survives once the action emission is properly fitted (the action-channel identification fingerprint, which is also a finite-sample test of the §4 spec's I6 identifiability claim). The combined v0.1+v0.2+v0.3 finding is positive evidence that the simplified §4 spec is identifiable in the harness when both channels are correctly modelled and the prior is informative enough — but the prior is still hard-coded at the generator's truth. The v0.5 actual identification test is now well-scoped.

Actions Cowork executes after human confirmation:

1. Populate `experiments/layer_2/hmm_validation_v0_3/notes.md` "Outcome: BETA_X_CONFIRMED" subsection with the produced numbers — the full V_prior × metrics table from `outputs/results.md`, plus a side-by-side comparison against v0.2's row-by-row V_prior=0.01 endpoint, plus a one-paragraph statement on (a) whether μ-RMSE moved when β_x was added (clean spec → no movement; coupled E-step → some movement), (b) whether Hamming(C) improved by the symmetric KL-asymmetry mechanism the v0.3 notes predict, (c) whether the v0.2 V_prior=0.1 Hamming(switch) peak survived β_x correction. Leave BETA_X_PARTIAL and BETA_X_NULL empty as a record of which branch was selected.

2. Create `experiments/layer_2/hmm_validation_v0_3/STATUS.md` summarizing the patch, the outcome, the v0.5 lower-bound identification target inherited from v0.2 (μ-RMSE ≈ 0.03, Hamming(T) and Hamming(C) both <0.10, ECE <0.08 on switching), and the next-step recommendation.

3. Stage v0.5 by creating `experiments/layer_2/hmm_validation_v0_5/` with the standard structure (`run.py`, `requirements.txt`, `README.md`, `notes.md`, `outputs/`, `decision_tree.md`). The v0.5 build incorporates three changes relative to v0.3: (a) **hierarchical Type-II ML outer loop with role index**, using a synthetic 2-role partition for now (role-level cohort N_role ≈ 30; budget calculation in v0.3 notes.md confirms the role-level posterior precision on `mu_role` is ≈ 690 nat-units, comfortably ≫ the per-executive prior precision needed to recover μ at the v0.2 V_prior=0.01 endpoint); (b) **covariate-dependent narrative emission with state-invariant slope**, parallel to the v0.3 β_x update on the action channel; (c) **Stephens KL on a 2-channel narrative emission**, replacing the cohort-folding `min(h0, h1)` Hamming with a principled label-alignment metric that uses both narrative components. v0.5's `notes.md` documents the v0.5 hypothesis (*"if the §4 spec is identifiable from data alone, hierarchical pooling with no truth-anchored prior should approach the v0.2 V_prior=0.01 / v0.3 β_x-confirmed endpoint within Monte Carlo tolerance"*), the expected lower-bound target inherited from v0.2 and v0.3, and three v0.5-specific outcome subsections. Wait for the human to run v0.5 before any further design-document work.

4. Do **not** modify the Layer 2 design document. BETA_X_CONFIRMED is an intermediate state — the design document is updated only by the *outcome* of v0.5.

5. Do **not** modify the research document. The §4.3.6 expected-values discrepancy remains an open follow-up item against the research-document maintainer regardless of v0.3's outcome; v0.3's outcome strengthens but does not resolve that follow-up.

6. v0.4 is reserved for whatever surfaces from v0.3 that needs further isolation before v0.5. Under BETA_X_CONFIRMED, no v0.4 is needed and the path is v0.3 → v0.5 directly. If the BETA_X_CONFIRMED criterion is met but the V_prior=0.1 Hamming(switch) peak survives β_x correction (i.e. the orthogonality test from `notes.md`'s "Carried-over diagnostic threads" section is non-trivial), record the surviving signal in STATUS.md as a v0.5 build risk to be tracked but not blocked on.

## Outcome B: BETA_X_PARTIAL

Hamming(T) at `V_prior = 0.01` drops by more than 0.05 (so β_x is doing some structural work) but plateaus above 0.10. Hamming(switch) and/or ECE may drop only partially, or one may drop while the other does not. β_x is part of the story but not all of it.

This verdict means a third structural mismatch is sharing responsibility for label recovery. The leading candidates, in approximate order of plausibility:

The action emission is fitted as a Bernoulli on `delta = -1` only, but the §4.1 spec calls for a categorical over `{-1, 0, +1}` matching the generator's full information set. The harness's `delta` generator emits values from `{-1, 0}` only (the generator never emits `+1`), so this is a missing-degree-of-freedom rather than a coverage issue at the data level — but the spec expects three degrees of freedom in the action emission, and conflating `delta = 0` with "not sell" rather than "not act" loses a discriminating signal. This is the most plausible third cause.

The opportunistic flag has no covariate slope but the generator's `p_op` differs by state with a `±0.5` log-odds gap (state T: 0.25, state C: 0.75). The harness fits a state-conditional intercept `xi_o[k]` only. If high-x slices in state T over-emit `o = 1` due to a generator-side correlation we haven't yet diagnosed, the missing covariate slope on the opportunistic channel could be a secondary cause. Less plausible than the categorical-vs-Bernoulli explanation but cheap to check inline.

The label-fixing post-hoc swap (`mu[0] > mu[1]` triggers a full reorder including `log_gamma`) is applied after EM converges. With a strong prior at V_prior = 0.01 the swap should rarely fire, but if it does fire it overwrites the EM-converged labels with a permutation that may not match the prior's anchor orientation. The `diag['label_swaps']` counter records this; we can read it from `outputs/results.json` without re-running.

Actions Cowork executes after human confirmation:

1. Populate `experiments/layer_2/hmm_validation_v0_3/notes.md` "Outcome: BETA_X_PARTIAL" subsection with the produced numbers, the magnitude of the Hamming(T) drop, the metrics that did and did not respond, and the per-cohort `label_swaps` count from `outputs/results.json` (this is the cheapest inline diagnostic and rules in or out the third candidate above immediately). Leave BETA_X_CONFIRMED and BETA_X_NULL empty.

2. Create `experiments/layer_2/hmm_validation_v0_3/STATUS.md` summarizing the partial outcome, the identified residual anomalous metric, and the next concrete step.

3. **Do not** stage v0.5. Stage v0.4 instead — a focused 1–2 hour diagnostic targeting the leading residual candidate. The v0.4 harness most likely replaces the Bernoulli on `delta` with a categorical over `{-1, 0, +1}` (or `{-1, 0}` if the generator is verified to never emit `+1`, in which case the change is a categorical with one observed level and the diagnostic falls through to candidate two). v0.4's hypothesis is *"if the missing categorical structure on the action emission is the third contributing cause, replacing Bernoulli with categorical should close the residual Hamming(T) gap that survives β_x"*. v0.4 inherits v0.3's full V_prior sweep harness and adds nothing else.

4. Do **not** modify the Layer 2 design document or the research document.

## Outcome C: BETA_X_NULL

Hamming(T) at `V_prior = 0.01` moves by less than 0.03. β_x is not the contributing cause. The Hamming(T) plateau survives both the v0.1 calibration patch and the v0.3 slope correction. The action-channel-attributable hypothesis space is exhausted at the level of single-line patches.

This verdict suggests the residual Hamming(T) is being driven by something that is not in the EM update equations themselves. Two candidates dominate:

The label-fixing post-hoc swap (`mu[0] > mu[1]` on the converged fit, which reorders all state-indexed quantities including `log_gamma`) is fighting the strong prior. With `V_prior = 0.01` the prior should pin `mu_T` and `mu_C` near the truth orientation, so the swap should rarely fire — but if it fires more than ~10–15% of the time on the always-T cohort, every fired swap is overwriting the EM-converged label with the opposite. This would inflate Hamming(T) by exactly the swap rate, which on 60 executives at ≈ 0.18 Hamming would correspond to a swap rate of ≈ 18%, plausibly visible in `diag['label_swaps']`.

The cohort-folding `min(h0, h1)` metric chooses whichever orientation produces lower Hamming, which means a cohort whose true labels are aligned with the prior orientation gets `h = h0`, and a cohort whose true labels are anti-aligned gets `h = h1`. For always-T cohorts, the true `z` is all zeros, so `h0 = mean(z_hat != 0)` and `h1 = mean(z_hat != 1) = 1 - h0`. The `min` is well-behaved when one orientation clearly wins, but if `z_hat` is roughly half-and-half across the time axis the metric reports `min(h0, 1-h0) = min(h0, 1-h0)` which is bounded above by 0.5 and tends to 0.5 only at the worst case. A high Hamming(T) like 0.188 means `z_hat` mismatches `z` (or `1-z`) on 18.8% of slices regardless of orientation choice — so the cohort-folding metric is not the immediate culprit unless the per-executive Hamming is bimodal (some executives near 0, others near 1).

Actions Cowork executes after human confirmation:

1. Populate `experiments/layer_2/hmm_validation_v0_3/notes.md` "Outcome: BETA_X_NULL" subsection with the produced numbers, side-by-side against v0.2 row-by-row, and the per-cohort `label_swaps` counts from `outputs/results.json` for the always-T cohort at every V_prior. Leave BETA_X_CONFIRMED and BETA_X_PARTIAL empty.

2. Create `experiments/layer_2/hmm_validation_v0_3/STATUS.md` summarizing the BETA_X_NULL outcome and explicitly recommending: *"v0.5 work should not proceed automatically. The next session is a half-day diagnostic discussion with the human to scope the investigation. Targets: (a) examine per-executive `label_swaps` rate in always-T at V_prior = 0.01 — if rate exceeds 15%, the label-fixing constraint is the culprit; (b) examine per-executive Hamming distribution — if it is bimodal, the cohort-folding metric is masking partial recovery; (c) instrument the EM loop with per-iteration μ̂ and prior-contribution traces if (a) and (b) are inconclusive. v0.4 and v0.5 are deferred until the inference loop is debugged."*

3. Surface the most-actionable diagnostic the human can run on v0.3 outputs without re-running the harness: print the per-cohort `label_swaps` counts and the per-executive Hamming distribution from `outputs/results.json` for the always-T cohort at V_prior = 0.01, flag the swap rate, and identify whether the per-executive Hamming distribution is unimodal or bimodal. Include this in `STATUS.md` under "Followups for human review."

4. Do **not** modify the Layer 2 design document, the research document, or stage v0.4 / v0.5 work. BETA_X_NULL means the inference loop is the priority; downstream design / spec work waits.

## How to invoke this runbook

Once the v0.3 run completes, paste the contents of `outputs/results.md` and the relevant rows of `outputs/results.json` back to Cowork along with a one-line read of which branch the result selects. Cowork ratifies or pushes back on the reading, and then executes the actions for the selected branch in the order listed above. No improvisation outside the documented branches.
