# HMM Validation v0 — Status Report

## Run summary

- Date executed: 2026-04-26
- Seed: 20260426
- Wall-clock time: 1185.2 s (≈ 19.75 minutes, single-core)
- Outcome: NUMBERS_DIFFER

The harness was extracted from §4.3.4 of the research document into `run.py`, dependencies (`numpy>=1.24`, `scipy>=1.10`) installed cleanly, and a single minimum compatibility fix applied to make the opportunistic-flag M-step run under `numpy >= 2.0` (`w @ scalar` is no longer accepted; replaced with the mathematically equivalent `w.sum() * scalar`). The full nine-cell sweep with K = 10 multi-start completed end-to-end in 1185.2 s on a single core, producing `outputs/results.json` and `outputs/results.md`. The harness ran cleanly. The threshold-validation result, however, **fails five of eight rows at the default sweep point**, with deltas to the §4.3.6 expected-output table that exceed the documented Monte Carlo tolerance (±0.02 on Hamming/ECE, ±0.05 on RMSE) by an order of magnitude.

This is a substantive empirical finding, not a runtime artifact. It is reported in §11 of the v0.2 design document and is the basis for the v0 specification's *not-yet-validated* status.

## Threshold pass/fail (default sweep point: β_sell = 0.3, a_chan = 0.6)

| Metric | Threshold | Produced (N=60) | Expected (§4.3.6) | Delta | MC tolerance | Verdict |
|---|---|---|---|---|---|---|
| Hamming (switching) | ≤ 0.20 | 0.298 | ~0.14 | +0.158 | ±0.02 | FAIL |
| Hamming (always-T) | ≤ 0.10 | 0.327 | ~0.05 | +0.277 | ±0.02 | FAIL |
| Hamming (always-C) | ≤ 0.10 | 0.201 | ~0.06 | +0.141 | ±0.02 | FAIL |
| ECE | ≤ 0.08 | 0.279 | ~0.05 | +0.229 | ±0.02 | FAIL |
| RMSE on $\mu$ | ≤ 0.15 | 0.277 | ~0.10 | +0.177 | ±0.05 | FAIL |
| RMSE on $P$ (Frob) | ≤ 0.20 | 0.161 | ~0.14 | +0.021 | ±0.05 | PASS |
| Multi-start fraction | ≥ 0.40 | 0.788 | ~0.55 | +0.238 | (not bounded) | PASS |
| Mean posterior entropy | ≤ 0.38 | 0.302 | ~0.32 | −0.018 | (not bounded) | PASS |

The transition-matrix Frobenius RMSE, the multi-start convergence fraction, and the mean posterior entropy reproduce the §4.3.6 expected values; the three Hamming metrics, ECE, and emission-mean RMSE do not. The pattern — transition kernel and convergence diagnostics OK, state-recovery and emission-recovery dramatically off — is consistent across all nine sweep cells (Hamming on the switching cohort lies in [0.257, 0.335] across the full grid, with no cell within ±0.10 of the 0.14 expected value). The robustness sweep does behave roughly as predicted at the *relative* level — degradation under high $\beta_{\text{sell}}$ and low $a_{\text{chan}}$ is on the predicted order of 0.03 to 0.05 — but the baseline against which that degradation is measured is shifted upward by approximately 0.16 in Hamming.

## Full sweep grid

| β_sell | a_chan | Hamming(switch) | ECE | μ_rmse | P_rmse | multistart_frac | entropy |
|---|---|---|---|---|---|---|---|
| 0.0 | 1.0 | 0.257 | 0.248 | 0.315 | 0.157 | 0.665 | 0.243 |
| 0.0 | 0.6 | 0.335 | 0.314 | 0.255 | 0.156 | 0.780 | 0.300 |
| 0.0 | 0.3 | 0.303 | 0.294 | 0.378 | 0.162 | 0.723 | 0.255 |
| 0.3 | 1.0 | 0.273 | 0.260 | 0.234 | 0.159 | 0.688 | 0.276 |
| 0.3 | 0.6 | 0.298 | 0.279 | 0.277 | 0.161 | 0.788 | 0.302 |
| 0.3 | 0.3 | 0.325 | 0.312 | 0.356 | 0.161 | 0.755 | 0.332 |
| 0.6 | 1.0 | 0.295 | 0.284 | 0.269 | 0.159 | 0.683 | 0.273 |
| 0.6 | 0.6 | 0.270 | 0.261 | 0.282 | 0.160 | 0.690 | 0.289 |
| 0.6 | 0.3 | 0.286 | 0.276 | 0.418 | 0.164 | 0.670 | 0.260 |

## Deviations from spec

The harness is a tractable approximation of the §4.1 specification, not the specification itself. `audit.md` enumerates 32 spec elements; the severity rollup is 11 EQUIV, 9 SIMPLIFIED, 10 MISSING, and 2 DEVIATION. The MISSING and DEVIATION rows concentrate on the action-emission decomposition (size, code, 10b5-1 components absent), the hierarchical structure (no Type-II ML outer loop, no role-level pool, transition kernel parameterized in probability space rather than logit space), and the diagnostics infrastructure (no `diagnostics.jsonl` written, several identifiability-flagging checks not exercised). The SIMPLIFIED rows concentrate on the narrative side (Gaussian rather than skew-normal, $C = 1$ rather than $C = 9$, no covariate slope) and on the action-direction emission (Bernoulli sell rather than three-way Categorical). The two DEVIATION rows are the action-channel availability prior (whose hard-coded emitter values do not match the generator's `T`-state rate) and the transition kernel (probability-space Dirichlet smoothing instead of logit-space hierarchical Gaussian).

The threshold-failure pattern is consistent with one or more of these deviations being responsible for the lost recovery. The first DEVIATION row — the action-availability prior mismatch between generator and emitter at state `T` — is a particularly likely culprit: the emitter's $\sigma(0.0) = 0.50$ disagrees with the generator's `T`-state availability rate of 0.40, which biases the likelihood at every always-T time slice and is the kind of small calibration error that compounds across 60 executives × ~38 time steps. The audit row was already SEVERITY=DEVIATION on theoretical grounds; the threshold-failure result elevates it from "should be expanded in v1" to "is plausibly the proximate cause of v0 failing its own thresholds." A v1 work item is to align the emitter with the generator and re-run.

## Recommended next actions

1. Investigate the root cause of the threshold failures. The DEVIATION row on the action-availability prior is the leading suspect. Other candidates: the no-slope state of `beta_x` in the EM (initialized to 0 and never updated, but the generator uses $\beta_{\text{sell}} = 0.3$ in the data-generating sell-direction logit, which the harness's EM cannot recover); the absence of a Stephens KL relabeling step (the harness uses argsort on `mu` only, which is correct for $C = 1$ but may interact poorly with the ECE and Hamming metrics under multi-modal posterior); and the possibility that the §4.3.6 expected values were themselves derived from a different version of the harness than the §4.3.4 code that ships in this document.

2. The Layer 2 v0.2 design document's §11 limitations subsection has been updated to report the NUMBERS_DIFFER outcome and the specific failing rows. The v0.2 document is in a defensible reviewable state with this update — the design is committed, the harness exists, the threshold result is honestly reported, and the next investigation is scoped.

3. v1 harness work is the right channel for the investigation. The audit document at `audit.md` enumerates the spec-vs-harness gaps that v1 must close; the threshold-failure root-cause analysis adds a sub-task to v1 that wasn't there before — verify each spec gap against the threshold-failure pattern and identify which gap (or gaps) account for the missing recovery. v1 should not assume the gaps are independent of the failure; they are the hypothesis space.

## Followups for human review

- The full harness execution against `--seed 20260426` produced numbers that fail five of eight thresholds. The single most-actionable next step is to investigate the action-availability calibration mismatch in `log_emissions` (the hard-coded `p_present = expit(np.where(k == 0, 0.0, -1.4))` in `run.py` line 50, against the generator's `A_d` rate of 0.4 in `T` and 0.2 in `C`). Aligning these would test whether this specific mismatch is the proximate cause.

- The §4.3.6 expected values in the research document at `docs/layers/layer_2/research/Insider Divergence Detection as Bayesian HMM Spec with Covariate-Dependent Emission.md` claim "the harness, run on the committed specification at the default sweep point, produces (within Monte Carlo noise of ±0.02 on Hamming/ECE and ±0.05 on RMSE)" the values in the expected-output table. Our run reproduces those expected values on three rows and contradicts them on five. Either the expected values are wrong, the harness in §4.3.4 differs from the harness that produced the §4.3.6 numbers, or there is a seed-dependent / numpy-version-dependent reproducibility issue. The research document is immutable per the task constraints, but a follow-up issue against the research document maintainer is appropriate.

- The single numpy-2.x compatibility fix (opportunistic-flag M-step Hessian) is mathematically equivalent to the original §4.3.4 code under numpy 1.x; it is documented in `notes.md`. We did not test on numpy 1.x (the workspace had numpy 2.2.6 installed). If the §4.3.6 expected values were derived under numpy 1.x and the fix has a subtle non-equivalence we are not seeing, that is one possible explanation for the threshold-failure pattern. Verifying by running the harness under numpy<2.0 with the original `w @ (p * (1-p))` line is a low-cost check.
