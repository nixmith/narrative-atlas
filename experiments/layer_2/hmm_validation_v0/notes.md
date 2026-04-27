# notes.md — `hmm_validation_v0`

## Reproducibility command

```
cd experiments/layer_2/hmm_validation_v0
pip install -r requirements.txt
python run.py --seed 20260426
```

The harness writes `outputs/results.json`, `outputs/results.md`, and (per §4.3.5 of the spec) is expected to write `outputs/diagnostics.jsonl`. The diagnostics file is not actually written by the §4.3.4 code; this is recorded in `audit.md` as a MISSING element.

## Minimum fix applied to the extracted code

The harness as transcribed from §4.3.4 runs under `numpy 1.x` but raises `ValueError: matmul: Input operand 1 does not have enough dimensions` under `numpy >= 2.0` at the opportunistic-flag M-step:

```
hess = -(w @ (p * (1-p))) - 1.0/V_prior
```

Here `xi_o[k]` is a scalar, so `p = expit(xi_o[k])` is a scalar and `p * (1-p)` is a scalar; `numpy 2.x` no longer treats `array @ scalar` as `array.sum() * scalar`. The mathematically equivalent fix is

```
hess = -(w.sum() * p * (1-p)) - 1.0/V_prior
```

which preserves the Newton update exactly. This is the only change to the extracted §4.3.4 code beyond the `--out` default redirection. No model logic, no parameter values, no thresholds, and no sweep-grid entries are altered.

## Run outcome

**Outcome: NUMBERS_DIFFER.**

The full nine-cell sweep with K = 10 multi-start completed end-to-end on `--seed 20260426` in 1185.2 s (≈19.75 minutes) on a single core in the user's environment. The harness ran cleanly. The threshold-validation result fails five of eight rows at the default sweep point, with deltas to the §4.3.6 expected-output table that exceed the documented Monte Carlo tolerance (±0.02 on Hamming/ECE, ±0.05 on RMSE) by an order of magnitude.

### Produced numbers vs §4.3.6 expected values (default sweep cell)

| Metric | Threshold | Produced (N=60) | Expected (§4.3.6) | Delta | MC tolerance | Verdict |
|---|---|---|---|---|---|---|
| Hamming (switching) | ≤ 0.20 | 0.298 | ~0.14 | +0.158 | ±0.02 | FAIL |
| Hamming (always-T) | ≤ 0.10 | 0.327 | ~0.05 | +0.277 | ±0.02 | FAIL |
| Hamming (always-C) | ≤ 0.10 | 0.201 | ~0.06 | +0.141 | ±0.02 | FAIL |
| ECE | ≤ 0.08 | 0.279 | ~0.05 | +0.229 | ±0.02 | FAIL |
| RMSE on $\mu$ | ≤ 0.15 | 0.277 | ~0.10 | +0.177 | ±0.05 | FAIL |
| RMSE on $P$ (Frob) | ≤ 0.20 | 0.161 | ~0.14 | +0.021 | ±0.05 | PASS |
| Multi-start fraction | ≥ 0.40 | 0.788 | ~0.55 | +0.238 | (n/a) | PASS |
| Mean posterior entropy | ≤ 0.38 | 0.302 | ~0.32 | −0.018 | (n/a) | PASS |

The transition-matrix Frobenius RMSE, the multi-start convergence fraction, and the mean posterior entropy reproduce within tolerance. The three Hamming metrics, the ECE, and the emission-mean RMSE do not. The pattern is consistent across the full sweep grid (Hamming on the switching cohort lies in [0.257, 0.335] across all nine cells; no cell is within ±0.10 of the 0.14 expected value).

The harness as transcribed does not modify model logic, parameter values, threshold table, or sweep grid; the only departure from §4.3.4 is the documented numpy-2.x compatibility fix. The threshold failures are produced by the harness exactly as specified.

### Sweep-grid robustness

The robustness sweep behaves roughly as predicted at the *relative* level. Increasing $\beta_{\text{sell}}$ from 0.0 to 0.6 at $a_{\text{chan}} = 0.6$ shifts Hamming(switch) from 0.335 to 0.270 (an *improvement*, contrary to the spec's expectation that high mechanical correlation degrades recovery). Decreasing $a_{\text{chan}}$ from 1.0 to 0.3 at $\beta_{\text{sell}} = 0.3$ shifts Hamming(switch) from 0.273 to 0.325 (a degradation of 0.052, consistent with the spec's expectation of a roughly 0.10 budget). The robustness *predictions* are roughly right; what is wrong is the *baseline* — the absolute Hamming level is shifted upward by approximately 0.16 across all cells.

### Hypotheses on the root cause

The threshold-failure pattern is concentrated in the state-recovery and emission-recovery metrics, while the transition-kernel and convergence diagnostics are within tolerance. This pattern is informative about where to look. The state-recovery metric (Hamming) and the posterior-calibration metric (ECE) both depend on the emission likelihood ranking $T$ vs $C$ correctly at each time slice; if the emission likelihoods are systematically miscalibrated, both metrics fail together. The emission-mean RMSE confirms that the EM is converging to emission means that are not the generator's true means.

Three concrete hypotheses, in descending order of likelihood:

The action-channel availability prior in the harness's `log_emissions` function is hard-coded to $\sigma(0.0) = 0.50$ in state `T` and $\sigma(-1.4) \approx 0.20$ in state `C`. The generator, in contrast, draws `A_d` from `Bernoulli(0.4)` in state `T` and `Bernoulli(0.2)` in state `C`. The state-`C` calibration is correct ($\sigma(-1.4) \approx 0.20 = 0.20$); the state-`T` calibration is wrong by 0.10 in absolute probability. This was already flagged in `audit.md` as severity DEVIATION before the threshold result came back. At every time slice, the absence-of-action factor enters the emission likelihood, so a systematic miscalibration here propagates to the state-decoding posterior. This is the leading suspect and the cheapest fix to test.

The covariate slope `beta_x` on the sell-direction logit is initialized to 0 in the harness and never updated in the M-step (no `beta_x` Newton update appears in `em_one`), but the generator injects mechanical price-volume coupling at $\beta_{\text{sell}} \in \{0.0, 0.3, 0.6\}$ in the data-generating logit. The harness fits a state-dependent intercept `nu[k]` only, which absorbs only the *average* sell propensity in each state and not the price-conditional sell propensity. This is consistent with the threshold-failure pattern *getting worse* at higher $\beta_{\text{sell}}$ in some cells — though the empirical pattern is mixed across the sweep grid and this hypothesis predicts a stronger and more monotone effect than is observed.

The expected values in §4.3.6 of the research document may have been derived from a different version of the harness than the one transcribed in §4.3.4. The expected-values text says "the harness, run on the committed specification at the default sweep point, produces (within Monte Carlo noise of ±0.02 on Hamming/ECE and ±0.05 on RMSE)" the §4.3.6 values, and "the actual numbers from the run are written to `results.json` and `results.md` and replace these expected values verbatim in the version of this document distributed with the v1.0 release." That phrasing reads as a placeholder anticipating substitution by the actual run, not a verified reproduction. If the §4.3.6 values were never verified against §4.3.4 code, the threshold-failure result is the verification step doing its job, and the conclusion is that the §4.3.6 values are wrong rather than that the §4.3.4 harness is wrong. This hypothesis cannot be tested without modifying the research document, which is outside scope; it can be raised with the research-document maintainer.

### What this means for downstream artifacts

The Layer 2 v0.2 design document's §11 limitations subsection is updated to report this outcome explicitly: the harness ran cleanly; the threshold table is failed on five of eight rows; the gap pattern points to the action-availability calibration mismatch as the leading suspect. The v0.2 document is in a defensible reviewable state with this update — the design is committed, the harness exists, the threshold result is honestly reported, and the next investigation is scoped.

The v1 harness work item gains a new sub-task: root-cause the threshold failures before expanding the model. The audit document at `audit.md` enumerates the spec-vs-harness gaps that v1 must close; those gaps are now also the hypothesis space for the threshold-failure investigation. v1 should not assume the gaps are independent of the failure.
