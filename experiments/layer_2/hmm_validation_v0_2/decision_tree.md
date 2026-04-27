# Decision tree — `hmm_validation_v0_2`

This file is the runbook for the round of work that follows the v0.2 run. The human runs the patched harness with `python run.py --seed 20260426`, observes the produced numbers in `outputs/results.md`, and selects one of the three branches below. Each branch prescribes the actions Cowork executes once the outcome has been reported and confirmed.

The three branches map directly to the three outcome subsections in `notes.md` (`STRUCTURAL_CONFIRMED`, `PARTIAL_CONFIRMED`, `ANOMALOUS`).

## Outcome A: STRUCTURAL_CONFIRMED

μ-RMSE drops monotonically with shrinking `V_prior` toward roughly 0.02–0.05 at `V_prior = 0.01`. Hamming on each cohort drops in lockstep with μ-RMSE. The convergence diagnostics — multi-start fraction and mean posterior entropy — drift only slightly relative to their `V_prior = 4.0` baselines.

This verdict means the v0/v0.1 threshold-failure pattern was caused by EM converging to a wrong local maximum that the default `V_prior = 4.0` Normal prior on `mu` was too weak to pull it out of. Anchoring the prior more strongly resolves the wrong-local-max problem when the prior mean *is* the truth. This is the structural-identification reading of the v0.1 STATUS.md. It is not a validation of the §4 specification — see the `notes.md` framing — but it tells us the v0.5 actual-identification test is the right next experiment, and gives us a lower-bound target it has to reach.

Actions Cowork executes after human confirmation:

1. Populate `experiments/layer_2/hmm_validation_v0_2/notes.md` "Outcome: STRUCTURAL_CONFIRMED" subsection with the produced numbers — the full `V_prior` × metrics table from `outputs/results.md`, plus a short paragraph noting the monotone shape of μ-RMSE and Hamming as `V_prior` shrinks. Leave the PARTIAL_CONFIRMED and ANOMALOUS subsections empty as a record of which branch was selected.

2. Create `experiments/layer_2/hmm_validation_v0_2/STATUS.md` summarizing the patch, the outcome, the lower-bound metrics from `V_prior = 0.01` (μ-RMSE, Hamming on each cohort, ECE), and the next-step recommendation: scope v0.5 (hierarchical Type-II ML pooling for `mu_prior`, covariate-slope EM update for `beta_x`, 2-channel narrative emission). The v0.2 `V_prior = 0.01` row becomes the **identification target** that v0.5's hierarchical pooling needs to approach. If v0.5's `mu_hat` recovery (with prior mean *learned* from the population, not hard-coded at truth) lands within ~0.03 of v0.2's `V_prior = 0.01` μ-RMSE, the §4 spec is empirically validated. If it lands materially worse, the spec has an identification gap that hierarchical pooling alone cannot close.

3. Do **not** modify the Layer 2 design document. STRUCTURAL_CONFIRMED is an intermediate state — the design document is updated only by the *outcome* of v0.5, not by the staging or outcome of v0.2.

4. Do **not** modify the research document. The §4.3.6 expected-values discrepancy flagged by v0.1 STATUS.md remains an open follow-up item against the research-document maintainer regardless of v0.2's outcome.

5. Stage v0.5 by creating `experiments/layer_2/hmm_validation_v0_5/` with the standard structure (`run.py`, `requirements.txt`, `README.md`, `notes.md`, `outputs/`, `decision_tree.md`). The v0.5 `run.py` carries the v0.1 calibration patch and adds three changes relative to v0.2: (a) hierarchical Type-II ML outer loop that re-estimates `mu_prior` and `V_prior` from the population fits each iteration; (b) M-step Newton update for `beta_x` (per the v0.1 decision-tree's PARTIAL_PASS branch); (c) two-component narrative emission. v0.5's `notes.md` documents the v0.5 hypothesis (*"if the §4 spec is identifiable from data alone, hierarchical pooling with no truth-anchored prior should approach the v0.2 `V_prior = 0.01` row within Monte Carlo tolerance"*), the expected lower-bound target inherited from v0.2, and three v0.5-specific outcome subsections. Wait for the human to run v0.5 before any further design-document work.

## Outcome B: PARTIAL_CONFIRMED

μ-RMSE drops with shrinking `V_prior` but plateaus above ~0.10 even at `V_prior = 0.01`. **And / or** some metric — most plausibly Hamming(T) or ECE — remains anomalous in a direction the prior cannot fix (for example: Hamming(T) stays above 0.10 even when μ-RMSE is small, or ECE on the switching cohort stays above 0.20).

This verdict means the prior-strength axis explains some but not all of the v0/v0.1 gap. A second structural mismatch shares responsibility. The leading candidates are:

- **Missing `beta_x` slope update.** The harness initialises `beta_x = 0.0` in `em_one` and never updates it, but the generator injects `Bernoulli(σ(±0.6 + 0.3·x))` action emissions. Under high covariate signal the harness's state-conditional intercept absorbs only the average sell propensity per state, leaving the price-conditional component unexplained. This shows up first in Hamming(T), because always-T episodes are the longest and most affected by the unmodelled slope.
- **Cohort-folding metric masking label orientation.** The harness's `min(h0, h1)` Hamming computation chooses whichever orientation produces a lower error. If the prior has begun to enforce the correct orientation in some episodes but not others, the folded metric will show artefactual structure. ECE is the best diagnostic for this, because the ECE alignment step uses the same per-episode orientation choice and any mis-alignment shows up there directly.

Actions Cowork executes after human confirmation:

1. Populate `experiments/layer_2/hmm_validation_v0_2/notes.md` "Outcome: PARTIAL_CONFIRMED" subsection with the produced numbers, identifying the plateau value of μ-RMSE and any anomalous metric. Leave STRUCTURAL_CONFIRMED and ANOMALOUS empty.

2. Create `experiments/layer_2/hmm_validation_v0_2/STATUS.md` summarizing the partial-confirmation outcome, the identified anomalous metric, and the next concrete step.

3. Do **not** stage v0.5 yet. The next session is a 1–2 hour focused diagnostic sub-experiment targeting the anomalous metric. Specifically: if the anomaly is in Hamming(T), the diagnostic is a single-cohort always-T fit at `V_prior = 0.01` with the `beta_x` Newton update applied (this was pre-staged in the v0.1 PARTIAL_PASS decision-tree branch and the code is ready to copy); if the anomaly is in ECE, the diagnostic is a print-out of per-episode label orientation choices to confirm whether the cohort-folding metric is masking a label-swap bug. The diagnostic stays in v0.2's `outputs/` (or a sibling sub-experiment directory like `hmm_validation_v0_2_diag/`) — the v0.5 stage waits until the residual anomaly is explained.

4. Do **not** modify the Layer 2 design document or the research document.

## Outcome C: ANOMALOUS

μ-RMSE remains above ~0.20 even at `V_prior = 0.01`, despite the prior mean being placed at the generator's truth. **Or** the metrics behave non-monotonically in `V_prior` in a way that cannot be explained by Monte Carlo noise on 60 executives per cohort.

This verdict means something more fundamental is wrong than either the calibration mismatch (ruled out by v0.1) or the prior-strength weakness hypothesis (ruled out by v0.2 if μ-RMSE cannot recover even when truth-anchored). Plausible structural explanations under this outcome:

- A label-swap step elsewhere in the EM loop is overwriting the prior anchor (e.g. the `mu[0] > mu[1]` swap is being applied after the prior pull instead of after free EM, in a way that prevents convergence).
- The cohort-folding metric is masking the true error (the underlying μ-recovery is fine, but the metric is computing the wrong thing).
- One of the EM update equations has a defect that prevents the prior from dominating even at `V_prior = 0.01` (e.g. a sign error, a missing prior term in `om` or `nu`, or a numerical-stability hack that bottoms out before the prior pull completes).
- The §4.1 specification itself does not survive synthetic-data testing in the way the harness implements it.

Actions Cowork executes after human confirmation:

1. Populate `experiments/layer_2/hmm_validation_v0_2/notes.md` "Outcome: ANOMALOUS" subsection with the produced numbers, the specific direction of the anomaly (μ-RMSE plateau value, monotonicity violations if any), and a side-by-side comparison against v0.1's default-cell metrics. Leave the STRUCTURAL_CONFIRMED and PARTIAL_CONFIRMED subsections empty.

2. Create `experiments/layer_2/hmm_validation_v0_2/STATUS.md` summarizing the ANOMALOUS outcome and explicitly recommending: *"v0.5 work should not proceed automatically. The next session is a half-day diagnostic discussion with the human to scope the investigation. Targets: (a) instrument the EM loop with per-iteration `mu` and prior contribution traces; (b) verify the `mu[0] > mu[1]` label-swap step is being applied after the prior pull, not before; (c) confirm the cohort-folding metric is computing what we think it is. v0.5 is deferred until the inference loop is debugged."*

3. Surface the most-actionable diagnostic the human can run on v0.2 outputs without re-running the harness: print the per-cohort `mu` recovery trajectory across `V_prior` values from `outputs/results.json`, flag any non-monotonic transitions, and identify whether the failure is concentrated in one cohort or uniform across all three. Include this in `STATUS.md` under "Followups for human review."

4. Do **not** modify the Layer 2 design document, the research document, or stage any v0.5 / v0.6 work. ANOMALOUS at v0.2 means the inference loop is the priority; downstream design / spec work waits.

## How to invoke this runbook

Once the v0.2 run completes, paste the contents of `outputs/results.md` and the relevant rows of `outputs/results.json` back to Cowork along with a one-line read of which branch the result selects. Cowork ratifies or pushes back on the reading, and then executes the actions for the selected branch in the order listed above. No improvisation outside the documented branches.
