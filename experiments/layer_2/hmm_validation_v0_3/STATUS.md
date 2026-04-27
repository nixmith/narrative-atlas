# HMM Validation v0.3 — Status Report

## Run summary

- Date executed: 2026-04-27
- Seed: 20260426
- Wall-clock: 796.0 s for `run.py` (V_prior sweep, +25% over v0.2's 634.5 s) and 133.9 s for `diagnose.py` (180 per-executive records at V_prior=0.01)
- Outcome: **BETA_X_NULL** (decision-tree branch C)

The v0.3 harness applies a single-block patch to v0.2: an ~11-line Newton-step M-step update for the state-invariant covariate slope `beta_x` in `em_one`'s inner EM loop, between the per-state `nu[k]` Newton block and the opportunistic-flag M-step. The patch is verified mathematically and matches the §4.1 spec's state-invariant slope. The full V_prior sweep harness from v0.2 is carried forward unchanged. The v0.1 calibration patch is also carried forward.

The hypothesis under test was: *if the missing β_x slope update is the second contributing cause to the v0.2 Hamming(T) plateau, fitting `beta_x` should drop Hamming(T) at `V_prior = 0.01` from 0.188 toward small values (~0.05–0.10).* The hypothesis is rejected on the metric criterion (Δ Hamming(T) at `V_prior = 0.01` = +0.002), and the diagnose.py companion run resolves three of the four readings of the strong null definitively.

## v0.3 results (default cell, beta_sell=0.3, a_chan=0.6)

| V_prior | Hamming(switch) | Hamming(T) | Hamming(C) | ECE | mu-RMSE | multistart | entropy |
|---|---|---|---|---|---|---|---|
| 0.01 | 0.242 | 0.190 | 0.168 | 0.233 | 0.029 | 0.645 | 0.331 |
| 0.1  | 0.290 | 0.228 | 0.151 | 0.260 | 0.136 | 0.805 | 0.340 |
| 1.0  | 0.262 | 0.265 | 0.245 | 0.250 | 0.321 | 0.670 | 0.288 |
| 4.0  | 0.269 | 0.280 | 0.237 | 0.254 | 0.338 | 0.727 | 0.275 |
| 64.0 | 0.281 | 0.307 | 0.261 | 0.260 | 0.455 | 0.673 | 0.277 |

Every metric at every V_prior moves within MC tolerance versus v0.2. The β_x update is a near-no-op on the harness's reported metrics. wall-clock increase confirms β_x is running; the metric stability says the per-slice posterior reweighting is too small to change label assignment.

## diagnose.py per-executive summary (V_prior=0.01)

| cohort | n | label_swaps_rate | multistart_mean | beta_x mean ± sd | Hamming min | q1 | median | mean | q3 | max |
|---|---|---|---|---|---|---|---|---|---|---|
| T | 60 | 0.000 | 0.668 | +73.999 ± 342.684 | 0.000 | 0.063 | 0.176 | 0.190 | 0.333 | 0.483 |
| C | 60 | 0.000 | 0.682 | -27.735 ± 629.000 | 0.000 | 0.057 | 0.149 | 0.168 | 0.250 | 0.500 |
| switch | 60 | 0.000 | 0.645 | +10.134 ± 416.156 | 0.000 | 0.143 | 0.241 | 0.242 | 0.371 | 0.481 |

The β_x cohort means and SDs are dominated by post-hoc Newton outliers in `derive_beta_x` (script-side, not `em_one`-side; see notes.md "Known diagnose.py limitation"). Trimmed medians after dropping `|β_x| ≥ 5`: +0.358 (T), +0.383 (C), +0.583 (switch), against truth 0.3.

## What v0.3 + diagnose.py established

- **β_x is fitted to truth on most executives but is not load-bearing for label recovery.** Trimmed cohort medians of converged β_x (0.36–0.58) sit in the right neighbourhood of truth 0.3. β_x · x has standard deviation ≈ 0.3 logits versus the ν_k intercept difference of 1.2 logits; the action emission's state separability is intercept-dominated, and β_x's per-slice contribution to the joint posterior is too small to change label assignment. The §4 spec's I6 identifiability claim is technically satisfied at finite samples; the spec is right to include β_x but it should not be expected to move the metric on its own.
- **The label-fixing-swap reading is dead.** `label_swaps_rate = 0.000` across 1800 multistart runs. Strong V_prior pins `mu` at truth orientation, so the post-hoc `mu[0] > mu[1]` reorder never fires.
- **Trace-length stratification is the structural identifiability bound.** Long always-T executives (T_i ≥ 50, n=21) have median Hamming **0.080** — passing the v0.1 threshold of 0.10 — while short always-T executives (T_i < 20) have median 0.300. The cohort-mean Hamming(T) of 0.190 is a length-mixture artifact, not a fundamental floor. corr(T_i, Hamming) on the T cohort is −0.332.
- **Dirichlet C-row asymmetric anchor is a real candidate.** The fitted `log_A` on always-T executives is essentially the Dirichlet prior `alpha_A = (50, 5)` because there are no observed C→T transitions to learn from. The prior's C-row equilibrium is (0.091, 0.909) versus truth (0.20, 0.80), so the smoothed posterior makes phantom-C excursions stickier than truth would allow. v0.4 is the counterfactual test that freezes `log_A` at the generator's truth and re-runs.

## Implications for v0.5

The trace-length finding is structurally compatible with the §4.9 output schema's `identifiability_flag` enum and the §15 cold-start logic: short-trace executives (T_i < 18 cold-start trigger; T_i < 20 in our diagnostic stratification) are anticipated to carry per-executive identifiability bounds that the spec handles by labelling them with reduced-confidence flags rather than fitting them to nominal accuracy. The v0.5 acceptance band naturally targets the well-identified subset (T_i ≥ 50, well above the cold-start trigger), where the v0.3 V_prior=0.01 endpoint already passes Hamming(T) ≤ 0.10.

Tentative v0.5 lower-bound identification target: Hamming(T) ≤ 0.10 on the T_i ≥ 50 subset, with documented degradation on the weakly-identified T_i 20–50 subset and explicit cold-start fallback at T_i < 18. Stephens KL on a 2-channel narrative emission replaces the cohort-folding `min(h0, h1)` metric, fixing the orientation-flip pathology surfaced on the C cohort short traces.

The v0.5 build proceeds only after the v0.4 result is in. If v0.4 confirms the Dirichlet C-row asymmetric anchor as the load-bearing residual factor, v0.5's transition design must incorporate role-level pooling on `log_A` (referenced in design document §4.1.2: hierarchical multinomial-logit transitions with role-level pooling) rather than relying on a single fixed Dirichlet anchor across the population. If v0.4 rules out the Dirichlet asymmetry, the residual Hamming(T) on T_i 20–50 executives is genuine per-slice ambiguity under the spec's emission overlap, and v0.5 either accepts the degradation or revisits the spec's emission design.

## Next concrete step

Run v0.4: **truth-frozen-A counterfactual.** Stage `experiments/layer_2/hmm_validation_v0_4/` with the same structure as v0.3, copy `run.py` and add one change: in `em_one`, replace the M-step that updates `log_A` from `xi_` and the Dirichlet prior with a fixed `log_A = np.log(np.array([[0.95, 0.05], [0.20, 0.80]]))` matching the generator's truth. Replay the V_prior sweep at the default cell. If Hamming(T) at V_prior=0.01 drops materially (target: into the 0.10–0.15 range, approaching the long-trace median of 0.080), the Dirichlet asymmetric anchor was the load-bearing residual factor and v0.5's transition design needs role-level pooling on `log_A`. If Hamming(T) is unchanged, the residual is genuine per-slice ambiguity on short and mid traces and v0.5 proceeds with the trace-length-stratified target.

Do **not** stage v0.5 until v0.4 lands.

## Followups for human review

- The `diagnose.py` post-hoc `derive_beta_x` numerical-stability issue (un-damped Newton against frozen `log_gamma`, no E-step feedback) is cosmetic. The trimmed-median β_x finding is load-bearing and unaffected. The proper fix is to expose β_x in `em_one`'s `best` dict in v0.5, not to patch `diagnose.py`.
- The cohort-folding `min(h0, h1)` metric pathology on always-C short traces (median Hamming 0.000 is a degenerate-`z_hat` artifact) is a v0.5 metric-design concern, addressed by the planned Stephens KL replacement on a 2-channel narrative emission.
- The §4.3.6 expected-values table follow-up at `docs/layers/layer_2/research/EXPECTED_VALUES_FOLLOWUP.md` is updated with the trace-length stratification as a third independent strand of evidence on top of the v0/v0.1 disagreement and the v0.2 internal inconsistency. The composite-prediction reading is strengthened: if §4.3.6's Hamming(T) ≈ 0.05 was derived from a long-trace sample (T_i ≥ 50), it is consistent with v0.3's measured median of 0.080 within MC tolerance; if it was derived from a representative `lognormal(log(38), 0.7)` sample (which is what §4.3.4 specifies), it is not consistent with any single configuration of the harness. The §4.3.6 row's cohort composition is now the load-bearing question for the research-document maintainer.
