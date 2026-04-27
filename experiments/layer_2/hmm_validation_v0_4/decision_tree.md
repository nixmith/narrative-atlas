# Decision tree — `hmm_validation_v0_4`

This file is the runbook for the round of work that follows the v0.4 run. The human runs the patched harness with `python run.py --seed 20260426`, observes the produced numbers in `outputs/results.md`, and selects one of the three branches below. Each branch prescribes the actions Cowork executes once the outcome has been reported and confirmed.

The three branches map directly to the three outcome subsections in `notes.md` (`TRANSITION_FLOOR_CONFIRMED`, `TRANSITION_FLOOR_PARTIAL`, `TRANSITION_FLOOR_NULL`).

## Outcome A: TRANSITION_FLOOR_CONFIRMED

Hamming(T) at V_prior = 0.01 drops to below 0.05 under frozen-truth-A. The Dirichlet C-row asymmetric anchor was the load-bearing residual factor on always-T cohorts. Hamming(C) and Hamming(switch) likely also improve; the magnitudes there are diagnostic but not branch-determining.

This verdict means hierarchical pooling on transitions is the v0.5 cure. The mechanism: in production, the always-T cohort's missing C→T transitions are filled in by transitions observed on the switching and always-C cohorts at the role-level pooling layer (per design document §4.1.2: hierarchical multinomial-logit transitions with role-level pooling). The pooling provides the data the always-T cohort lacks individually, breaking the Dirichlet-prior dominance that v0.4 just confirmed is the load-bearing factor.

Actions Cowork executes after human confirmation:

1. Populate `experiments/layer_2/hmm_validation_v0_4/notes.md` "Outcome: TRANSITION_FLOOR_CONFIRMED" subsection with the produced numbers — the full V_prior × metrics table, plus a side-by-side comparison against v0.3 row-by-row, plus a one-paragraph statement on (a) the magnitude of the Hamming(T) drop at V_prior=0.01, (b) whether Hamming(C) and Hamming(switch) also dropped (and by how much), (c) whether μ-RMSE moved when transitions were frozen (clean spec → no movement; coupled E-step → some movement, possibly because forward-backward smoothing at the right transition matrix sharpens per-slice posteriors which feed back into the narrative M-step). Leave TRANSITION_FLOOR_PARTIAL and TRANSITION_FLOOR_NULL empty as a record of which branch was selected.

2. Create `experiments/layer_2/hmm_validation_v0_4/STATUS.md` summarizing the patch, the outcome, the v0.5 lower-bound identification target inherited from v0.2/v0.3/v0.4, and the next-step recommendation.

3. Stage v0.5 by creating `experiments/layer_2/hmm_validation_v0_5/` with the standard structure. The v0.5 build incorporates **hierarchical pooling on transitions as a core feature alongside hierarchical pooling on emission means**, per design document §4.1.2. The v0.5 Hamming target is the original ≤0.10 with confidence rooted in the v0.4 result. Specifically: (a) hierarchical Type-II ML outer loop with role index using a synthetic 2-role partition; (b) covariate-dependent narrative emission with state-invariant slope, parallel to the v0.3 β_x update on the action channel; (c) hierarchical multinomial-logit transitions with role-level pooling on `log_A`, replacing the v0.4 frozen-truth-A counterfactual with the production mechanism; (d) Stephens KL on a 2-channel narrative emission, replacing the cohort-folding `min(h0, h1)` Hamming with a principled label-alignment metric. v0.5's `notes.md` documents the v0.5 hypothesis, the expected lower-bound target inherited from v0.4, and three v0.5-specific outcome subsections. Wait for the human to run v0.5 before any further design-document work.

4. Do **not** modify the Layer 2 design document. TRANSITION_FLOOR_CONFIRMED is an intermediate state — the design document is updated only by the *outcome* of v0.5.

5. Update `docs/layers/layer_2/research/EXPECTED_VALUES_FOLLOWUP.md` with a fourth subsection "v0.4 update — transition-matrix-identification floor" noting that the cohort-composition-mismatch reading from v0.3 is now refined: the §4.3.6 expected Hamming(T) ≈ 0.05 may have been generated under a frozen-truth-A configuration of the harness (rather than the §4.3.4 EM-fitted-with-Dirichlet-prior configuration), which is a fourth possible composition-mismatch hypothesis on top of the long-trace-sample reading. This gives the research-document maintainer two specific testable hypotheses for the §4.3.6 row's provenance.

## Outcome B: TRANSITION_FLOOR_PARTIAL

Hamming(T) at V_prior = 0.01 drops by more than 0.10 (so transition-matrix identification is doing material work) but plateaus above 0.05. The Dirichlet asymmetric anchor accounts for most but not all of the v0.3 gap. The most plausible residual is short-trace per-slice ambiguity (reading 3 from v0.3 BETA_X_NULL), which freezing A at truth doesn't fix because it doesn't add data to short-trace executives.

This verdict means v0.5 proceeds with the original target ≤0.10, but the STATUS.md must explicitly track the residual short-trace risk and propose a backup acceptance band of ≤0.15.

Actions Cowork executes after human confirmation:

1. Populate `experiments/layer_2/hmm_validation_v0_4/notes.md` "Outcome: TRANSITION_FLOOR_PARTIAL" subsection with the produced numbers, the magnitude of the Hamming(T) drop at V_prior=0.01, the magnitude of the residual gap (e.g. "Hamming(T) dropped from 0.190 to 0.075 — a 0.115 reduction, but plateauing above the 0.05 BETA_X_CONFIRMED-equivalent threshold"), and a side-by-side comparison against v0.3. Leave TRANSITION_FLOOR_CONFIRMED and TRANSITION_FLOOR_NULL empty.

2. Create `experiments/layer_2/hmm_validation_v0_4/STATUS.md` summarizing the partial outcome and the residual short-trace risk.

3. Stage v0.5 with the original target ≤0.10 but with a **documented risk** tracked in v0.5's STATUS.md: hierarchical pooling on transitions may close most but not all of the gap, and a backup acceptance band of ≤0.15 may be needed if v0.5 lands above 0.10. The v0.5 build is otherwise identical to the TRANSITION_FLOOR_CONFIRMED version.

4. Do **not** modify the Layer 2 design document or the research document.

## Outcome C: TRANSITION_FLOOR_NULL

Hamming(T) at V_prior = 0.01 stays above 0.15 under frozen-truth-A. The plateau is deeper than transition-matrix identification. Reading (3) from v0.3 BETA_X_NULL — short-trace executives carry an inherent identifiability bound under weak forward-backward smoothing regardless of model parameters — is now the leading candidate, and reading (4) is decisively ruled out.

This verdict means the v0.5 acceptance band needs to be revised to a length-stratified target rather than a cohort-mean target. The half-day diagnostic discussion is mandatory before v0.5 staging.

Actions Cowork executes after human confirmation:

1. Populate `experiments/layer_2/hmm_validation_v0_4/notes.md` "Outcome: TRANSITION_FLOOR_NULL" subsection with the produced numbers, the residual Hamming(T) at V_prior=0.01, and the side-by-side against v0.3 (which should show essentially no improvement). Leave TRANSITION_FLOOR_CONFIRMED and TRANSITION_FLOOR_PARTIAL empty.

2. Create `experiments/layer_2/hmm_validation_v0_4/STATUS.md` summarizing the TRANSITION_FLOOR_NULL outcome and explicitly recommending: *"v0.5 work should not proceed automatically. The next session is a half-day diagnostic discussion with the human. Targets: (a) instrument the EM loop with per-iteration μ̂, β_x, and per-slice gamma trajectory traces to identify whether the failure is at convergence or in the convergence trajectory; (b) re-examine the cohort-folding `min(h0, h1)` metric for masking bimodal failure (the v0.3 diagnose.py per-executive Hamming distribution showed wide spread); (c) consider whether the spec's identification claim itself needs revision before v0.5 build, especially the cold-start fallback at T_i < 18 may need to be more aggressive (extending to T_i < 30 or similar). v0.5 build is deferred."*

3. Surface the most-actionable diagnostic the human can run on v0.4 outputs without re-running the harness: read `outputs/results.json` for the per-cohort metrics and confirm that the Hamming-vs-T_i correlation is similar to v0.3's −0.332 on the always-T cohort. If the correlation strengthens (say, to −0.5 or below), short-trace identifiability is more clearly the dominant story; if the correlation weakens, the failure mode has shifted and a different diagnostic is needed.

4. Do **not** modify the Layer 2 design document, the research document, or stage v0.5 work. TRANSITION_FLOOR_NULL means the inference loop or the metric design has a deeper issue that needs human-led scoping before further patching.

## How to invoke this runbook

Once the v0.4 run completes, paste the contents of `outputs/results.md` and the relevant rows of `outputs/results.json` back to Cowork along with a one-line read of which branch the result selects. Cowork ratifies or pushes back on the reading, and then executes the actions for the selected branch in the order listed above. No improvisation outside the documented branches.
