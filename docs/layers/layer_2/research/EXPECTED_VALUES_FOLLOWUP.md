# §4.3.6 expected-values table — verification follow-up

The §4.3.6 expected-values table in `Insider Divergence Detection as Bayesian HMM Spec with Covariate-Dependent Emission.md` reports, for the default sweep cell (beta_sell = 0.3, a_chan = 0.6) and within Monte Carlo tolerance (±0.02 on Hamming/ECE, ±0.05 on RMSE), expected values of approximately Hamming(switch) 0.14, Hamming(T) 0.05, Hamming(C) 0.06, ECE 0.05, mu-RMSE 0.10, P-RMSE 0.14, multistart fraction 0.55, entropy 0.32.

Two seeded runs of the §4.3.4 harness against `--seed 20260426` have produced substantively different numbers on five of these eight rows. The transition-kernel RMSE, multistart fraction, and posterior entropy reproduce within tolerance. The three Hamming metrics, ECE, and mu-RMSE do not, by margins of 0.10 to 0.28 — an order of magnitude beyond MC tolerance.

The v0 run is recorded at `experiments/layer_2/hmm_validation_v0/` (NUMBERS_DIFFER, 1185.2 s wall-clock). The v0.1 run, with a controlled patch calibrating the action-availability prior to match the generator (the only DEVIATION-severity audit row that could plausibly account for the gap), is recorded at `experiments/layer_2/hmm_validation_v0_1/` (FAIL, 1241.5 s wall-clock). The patch moved metrics by exactly the magnitudes per-slice nat-arithmetic predicted, including the asymmetric direction reversal between always-T and always-C cohorts driven by the KL-distance shrinkage between Bernoulli(0.4) and Bernoulli(0.2) versus Bernoulli(0.5) and Bernoulli(0.2). The patch behaved as predicted; the residual gap is not calibration-attributable.

The simplest remaining hypothesis is that the §4.3.6 values were not produced by the §4.3.4 code. Possible causes: (a) the values were predictions written before the harness was finalized, (b) the values were produced by a different version of the harness than the one shipped in §4.3.4, (c) the values were produced under a different numpy/scipy version than the one specified in the research document. None of these is testable without modifying the research document, which is immutable per the project's working rules.

## v0.2 update — internal inconsistency in the §4.3.6 row

A third seeded run of the harness has been executed at `experiments/layer_2/hmm_validation_v0_2/` (V_prior-only sweep at the default cell, 634.5 s wall-clock, `--seed 20260426`). The v0.2 result is internally informative beyond the v0/v0.1 disagreement: the harness was swept across `V_prior ∈ {0.01, 0.1, 1.0, 4.0, 64.0}` with the prior mean placed at the generator's truth, which produces the cleanest possible recovery of `mu` the harness can deliver at the V_prior = 0.01 endpoint. The full V_prior × metrics table from v0.2 is:

| V_prior | Hamming(switch) | Hamming(T) | Hamming(C) | ECE | mu-RMSE | multistart | entropy |
|---|---|---|---|---|---|---|---|
| 0.01 | 0.241 | 0.188 | 0.160 | 0.229 | 0.029 | 0.667 | 0.338 |
| 0.1  | 0.297 | 0.237 | 0.151 | 0.270 | 0.139 | 0.798 | 0.341 |
| 1.0  | 0.257 | 0.252 | 0.243 | 0.247 | 0.320 | 0.647 | 0.290 |
| 4.0  | 0.256 | 0.281 | 0.254 | 0.244 | 0.335 | 0.688 | 0.283 |
| 64.0 | 0.281 | 0.299 | 0.262 | 0.255 | 0.441 | 0.692 | 0.279 |

The §4.3.6 expected values for the same cell are mu-RMSE ≈ 0.10 with Hamming(T) ≈ 0.05 (jointly).

These two numbers do not co-occur at any V_prior in the actual harness behaviour. mu-RMSE = 0.139 occurs at V_prior = 0.1, where Hamming(T) = 0.237. mu-RMSE = 0.029 occurs at V_prior = 0.01, where Hamming(T) = 0.188. The mu-RMSE column is monotone-decreasing in 1/V_prior; Hamming(T) is also approximately monotone-decreasing in 1/V_prior; they do not cross at the §4.3.6 expected joint value, and there is no V_prior between 0.01 and 0.1 at which the harness could plausibly produce mu-RMSE ≈ 0.10 with Hamming(T) ≈ 0.05 — by interpolation, the V_prior that delivers mu-RMSE ≈ 0.10 sits between 0.01 and 0.1 but Hamming(T) at that interpolated point is bounded below by 0.188 (the V_prior = 0.01 endpoint), still ~3.7× the §4.3.6 value.

The v0.3 stage at `experiments/layer_2/hmm_validation_v0_3/` adds an EM update for the covariate slope `beta_x` (the leading missing-piece candidate from the v0.2 PARTIAL_CONFIRMED outcome), and may reduce the Hamming(T) lower bound somewhat. But even the most optimistic v0.3 outcome would have to deliver Hamming(T) ≈ 0.05 at mu-RMSE ≈ 0.10 jointly to reproduce the §4.3.6 values, which would require the action-channel-attributable residual to drop by ~0.13 and the narrative-channel residual to stay at ~0.10 simultaneously. That joint pattern is not predicted by the structural-identification analysis.

The §4.3.6 row is therefore not a single harness run. It is most plausibly a composite — independent rough estimates of each individual row (mu-RMSE estimated from one piece of analysis, Hamming(T) from another, etc.), or pure prediction. This is a stronger finding than the original v0/v0.1 observation that two seeded runs disagree with the table on five of eight rows: the v0.2 sweep shows that no single configuration of the harness can reproduce the §4.3.6 row jointly, regardless of seed, regardless of V_prior, and regardless of any plausible patch to the harness that closes the action-channel gap (v0.3) or the calibration gap (v0.1).

Pending maintainer review, the §4.3.6 values should be treated as **predictions, possibly composite predictions across rows**, rather than measurements. The v0, v0.1, v0.2, and v0.3 results in `experiments/layer_2/` are the actual measurements of the §4.3.4 code.

## v0.3 + diagnose.py update — trace-length stratification

A fourth seeded run of the harness with a covariate-slope `beta_x` Newton M-step (the leading missing-piece candidate from v0.2 PARTIAL_CONFIRMED) has been executed at `experiments/layer_2/hmm_validation_v0_3/` (BETA_X_NULL outcome, 796.0 s wall-clock for the V_prior sweep, 133.9 s for a per-executive `diagnose.py` companion at V_prior = 0.01). The β_x update produced a near-no-op on every reported metric (Δ Hamming(T) at V_prior=0.01 = +0.002, within MC tolerance), but the diagnose.py per-executive data revealed a structural finding beyond what the cohort-mean Hamming(T) shows: **the failure mode is a length-mixture artifact, not a uniform per-slice floor**. Per-executive Hamming on the v0.3 always-T cohort at V_prior = 0.01 stratified by T_i:

| T_i bucket | n | Hamming median |
|---|---|---|
| T_i < 20 | 11 | 0.300 |
| T_i 20–50 | 28 | 0.205 |
| T_i ≥ 50 | 21 | **0.080** |

The corr(T_i, Hamming) on the always-T cohort is **−0.332**. Long always-T executives (T_i ≥ 50) have median Hamming = 0.080, **passing the v0.1 threshold of 0.10**. The cohort-mean Hamming(T) of 0.190 averages short, mid, and long executives where short-trace identifiability is the limiting factor.

This further refines the §4.3.6 internal-inconsistency reading. If §4.3.6's Hamming(T) ≈ 0.05 was derived from a long-trace sample (T_i ≥ 50), it is consistent with v0.3's measured median of 0.080 within Monte Carlo tolerance. If it was derived from a representative cohort drawn from `T_dist = lognormal(log(38), 0.7)` clipped to `[10, 200]` (which is what §4.3.4 explicitly specifies), it is not consistent with any single configuration of the harness — the cohort-mean Hamming(T) under that T_dist averages to ~0.19 regardless of seed, V_prior, β_x, or any other harness knob the v0–v0.3 series has tested. The cohort composition assumed when §4.3.6's expected values were generated is now the load-bearing question for the research-document maintainer.

This is a third independent strand of evidence on top of the v0/v0.1 seeded-run disagreement and the v0.2 internal inconsistency between μ-RMSE and Hamming(T) values that do not co-occur at any V_prior. Each strand independently rules out a class of explanations for the §4.3.6 discrepancy, and together they make the composite-prediction reading the simplest remaining hypothesis. The v0.3 strand specifically identifies the most plausible composition mismatch: a §4.3.6 sample that effectively over-weights long traces (or trims short traces) relative to the §4.3.4 generator's clipped-lognormal T_dist.

## v0.4 update — transition-matrix-fitting axis

A fifth seeded run of the harness has been executed at `experiments/layer_2/hmm_validation_v0_4/` (TRANSITION_FLOOR_PARTIAL_PLUS_C_TRAJECTORY_PATHOLOGY outcome, 776.6 s wall-clock, `--seed 20260426`). v0.4 deletes the transition-matrix M-step in `em_one`, freezing `log_A` at the canonical generator values `[[0.95, 0.05], [0.20, 0.80]]` throughout EM. This is a counterfactual diagnostic — production cannot freeze A at truth — and its purpose is to test whether the v0.3 BETA_X_NULL Hamming(T) plateau was driven by the EM's inability to identify the transition matrix on always-T data.

Hamming(T) at V_prior = 0.01 dropped from 0.190 (v0.3) to **0.120** (v0.4) — a 64% closure of the gap from v0.3's cohort mean to v0.3's long-trace floor of 0.080. The Dirichlet C-row asymmetric anchor (prior equilibrium (0.091, 0.909) versus truth (0.20, 0.80)) was load-bearing on the always-T cohort. Hamming(switch) improved by 0.054. μ-RMSE held at 0.029. The v0.4 finding is a clean confirmation that the transition-matrix-fitting axis is identifiable-floor-binding on always-T cohorts, and that the spec's hierarchical multinomial-logit transition kernel — which provides cross-cohort transition observations to break the Dirichlet anchor's dominance on always-T — is the correct production mechanism.

This refines the cohort-composition-mismatch reading from v0.3 along a fourth axis: the §4.3.6 expected values may have been generated under any combination of (a) a long-trace cohort sample, (b) a frozen-truth-A or hierarchically-pooled-A configuration of the harness, (c) a different multistart-initialization scheme that breaks the v0.4-surfaced uniform multistart trap, and (d) the §4.3.4-as-shipped EM-fitted-Dirichlet-A code on the §4.3.4-specified `T_dist` sample. The v0.x record now rules out (d) with high confidence: no single-knob change to the §4.3.4-as-shipped code reproduces the §4.3.6 row, and v0.4 confirms that the Dirichlet-A configuration specifically is incompatible with §4.3.6's expected Hamming(T). The §4.3.6 row was either generated under one of (a)/(b)/(c) — a non-§4.3.4 configuration — or is a composite prediction across rows. Either way, the §4.3.6 row's provenance is the load-bearing question for the research-document maintainer.

This is the fourth independent strand of evidence on top of the v0/v0.1 seeded-run disagreement, the v0.2 internal inconsistency between μ-RMSE and Hamming(T), and the v0.3 trace-length stratification. The composite-prediction reading (or the non-§4.3.4-configuration reading) is the simplest remaining hypothesis. Each strand independently rules out a class of explanations.

Process recommendation for future research documents: before any number is quoted as harness output in a research document, the harness should be run end-to-end and the actual measurement substituted into the document, tagged with the producing commit SHA. Predictions written before harness execution should be marked as such. This conversation's discipline of running the harness as the verification step caught the issue cleanly; the recommendation is to make that discipline upstream of research-document publication rather than downstream.
