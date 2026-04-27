# Decision tree — `hmm_validation_v0_1`

This file is the runbook for the round of work that follows the v0.1 run. The human runs the patched harness with `python run.py --seed 20260426`, observes the produced numbers in `outputs/results.md`, and selects one of the three branches below. Each branch prescribes the actions Cowork executes once the outcome has been reported and confirmed.

## Outcome A: PASS

All eight rows in the pass/fail table show PASS, with the five previously-failing metrics (`hamming_switch`, `hamming_T`, `hamming_C`, `ece`, `mu_rmse`) now within the documented ±0.02 / ±0.05 Monte Carlo tolerance of the §4.3.6 expected values.

This verdict means the v0 calibration mismatch was the proximate cause of the threshold failures. The harness as currently constituted (after the v0.1 patch) empirically validates the tractable approximation of §4.1 within the documented tolerance. Full-spec validation remains deferred to the v1 harness expansion, which closes the SIMPLIFIED and MISSING audit rows; v1 work proceeds as planned but no longer carries an emergency-investigation scope.

Actions Cowork executes after human confirmation:

1. Update `docs/layers/layer_2/Layer2_Insider_Divergence.md` §11.2 limitations subsection. Add a paragraph stating that the v0.1 patch resolved the v0 threshold failures, that the action-availability calibration mismatch was the proximate cause, and that the v0 harness as currently constituted (after the v0.1 patch) empirically validates the tractable approximation of §4.1 within the documented Monte Carlo tolerance. Mark the v0 result as "tractable-approximation validation passing; full-spec validation deferred to v1 harness."

2. Update the Layer 2 design document version from v0.2 to v0.3. Add a changelog entry describing the patch (one-line calibration alignment of the action-channel availability prior in `log_emissions`), the outcome (all eight thresholds passing at the default sweep point), and the corrected validation status (tractable-approximation validation complete; full-spec validation deferred to v1).

3. Populate `experiments/layer_2/hmm_validation_v0_1/notes.md` "Outcome: PASS" subsection with the produced numbers, side-by-side with the §4.3.6 expected values, and a one-paragraph statement that the hypothesis is confirmed. Leave the PARTIAL PASS and FAIL subsections empty as a record of which branch was selected.

4. Create `experiments/layer_2/hmm_validation_v0_1/STATUS.md` summarizing the patch, the outcome, and the next-step recommendation: Threads B (SEC-enforcement-labeled supervised pipeline) and C (speaker-attributed Layer 4) are now unblocked at the spec level; v1 harness expansion (closing the SIMPLIFIED and MISSING audit rows) proceeds as planned.

## Outcome B: PARTIAL PASS

Some previously-failing metrics now pass; others still fail. This verdict means the calibration mismatch was a contributing cause but not the only cause; the audit's MISSING and DEVIATION rows still hold the remaining hypothesis space.

The leading next-suspect, based on the v0 `notes.md` analysis, is the missing covariate-slope `beta_x` update in EM. The harness initializes `beta_x = 0.0` in `em_one` and never updates it in any M-step, but the generator injects mechanical price-volume coupling at $\beta_{\text{sell}} \in \{0.0, 0.3, 0.6\}$. The harness fits a state-dependent intercept `nu[k]` only, which absorbs the average sell propensity per state but not the price-conditional sell propensity. Under high $\beta_{\text{sell}}$, the missing slope update should produce a worse emission fit than under low $\beta_{\text{sell}}$.

Actions Cowork executes after human confirmation:

1. Populate `experiments/layer_2/hmm_validation_v0_1/notes.md` "Outcome: PARTIAL PASS" subsection with the produced numbers, identifying which metrics passed and which still failed. Leave the PASS and FAIL subsections empty as a record of which branch was selected.

2. Do not update the Layer 2 design document. Partial pass is an intermediate state and the design document is not re-versioned until the investigation completes.

3. Stage v0.2 by creating `experiments/layer_2/hmm_validation_v0_2/` with the same structure as v0.1 (`run.py`, `requirements.txt`, `README.md`, `notes.md`, `outputs/`, `decision_tree.md`). The v0.2 `run.py` carries the v0.1 patch plus a single additional change: an M-step update for `beta_x`. The minimal update is one Newton step per outer EM iteration, summed over both states (since the slope is state-invariant in the spec):

   ```python
   # After the per-state nu[k] updates, before opportunistic flag:
   # M-step: beta_x (state-invariant slope, one Newton step)
   grad_beta = 0.0
   hess_beta = 0.0
   for k in range(K):
       w = gamma[:, k] * A_d
       if w.sum() < 1.0:
           continue
       p = expit(nu[k] + beta_x * x); y = (delta == -1).astype(float)
       grad_beta += w @ ((y - p) * x)
       hess_beta += -(w @ (p * (1-p) * x * x)) - 1e-3
   beta_x = beta_x - grad_beta / hess_beta
   ```

   This is the only change v0.2 introduces relative to v0.1. v0.2's `notes.md` documents the unified diff against v0.1, the hypothesis (*"if the missing covariate-slope update is the second contributing cause, fitting `beta_x` should close the remaining gap"*), and the reproducibility command. v0.2 has its own `decision_tree.md` mirroring this file's structure, with the three branches updated for v0.2's hypothesis. The human runs v0.2; Cowork waits for the result.

4. Create `experiments/layer_2/hmm_validation_v0_1/STATUS.md` summarizing the partial-pass outcome, the staging of v0.2, and the next concrete step (the human runs `python run.py --seed 20260426` in the v0.2 directory).

## Outcome C: FAIL

No metric meaningfully improves over v0, or the patched results are worse. This verdict means the calibration mismatch was not the proximate cause and the failure pattern is being driven by something more fundamental than any single audit row.

The most plausible structural explanations under this outcome: the missing hierarchical Type-II ML outer loop (the harness fits each executive independently with a fixed prior whose mean equals the generator's true mean — the test is biased toward easy recovery, and yet still fails); the absence of any covariate-slope update in EM (more serious if Outcomes A and B both indicate calibration is not the issue); or a deeper model-specification mismatch where the spec itself (not the harness's approximation of it) does not yet survive the synthetic-data test.

Actions Cowork executes after human confirmation:

1. Populate `experiments/layer_2/hmm_validation_v0_1/notes.md` "Outcome: FAIL" subsection with the produced numbers and a side-by-side comparison against v0. Leave the PASS and PARTIAL PASS subsections empty as a record of which branch was selected.

2. Do not update the Layer 2 design document. Do not stage v0.2. A FAIL outcome at v0.1 indicates the hypothesis space requires a half-day diagnostic session with the human before any further patch work is justified.

3. Create `experiments/layer_2/hmm_validation_v0_1/STATUS.md` summarizing the FAIL outcome and explicitly recommending: *"v0.2 patch work should not proceed automatically. The next session should be a diagnostic discussion with the human to scope the investigation, examine the v0.1 diagnostics file (if produced) for evidence of EM convergence pathologies, and decide whether the next experiment is a deeper harness rewrite or a re-examination of the §4.1 specification itself."*

4. Surface the most-actionable diagnostic the human can run on the v0.1 outputs without re-running the full harness: *"Compare the per-cohort emission-mean RMSE against the per-cohort entropy and multi-start fraction. If RMSE is high but entropy is low and multi-start fraction is high, the EM is converging confidently and consistently to a wrong answer — which points to a structural identification problem rather than an optimization problem."* Include this in `STATUS.md` under "Followups for human review."

## How to invoke this runbook

Once the v0.1 run completes, paste the contents of `outputs/results.md` and the produced `pass_fail` dictionary from `outputs/results.json` back to Cowork along with a one-line read of which branch the result selects. Cowork ratifies or pushes back on the reading, and then executes the actions for the selected branch in the order listed above. No improvisation outside the documented branches.
