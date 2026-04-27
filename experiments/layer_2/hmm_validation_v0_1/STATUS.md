# HMM Validation v0.1 — Status Report

## Run summary

- Date executed: 2026-04-27
- Seed: 20260426
- Wall-clock time: 1241.5 s (≈ 20.7 minutes, single-core)
- Outcome: FAIL (decision-tree branch C)

The v0.1 harness applies a single-line patch to the v0 harness's `log_emissions` function, calibrating the action-channel availability prior in state $T$ from the hard-coded $\sigma(0.0) = 0.50$ to the generator's true rate of 0.40 (the state-$C$ rate of 0.20 was already correctly calibrated under v0). The patch was verified mathematically before the run: `np.log(0.4 / 0.6)` and `np.log(0.2 / 0.8)` evaluate to logits whose sigmoid is exactly 0.40 and 0.20 respectively. No other line in `run.py` was changed.

The hypothesis under test was: *if the action-availability prior mismatch is the proximate cause of the v0 threshold failures, calibrating the prior to match the generator should move all five failing metrics into PASS at the default sweep point.* The hypothesis is rejected.

## Threshold pass/fail (default sweep cell, β_sell = 0.3, a_chan = 0.6)

| Metric | Threshold | v0 | v0.1 | Δ | v0 verdict | v0.1 verdict |
|---|---|---|---|---|---|---|
| Hamming (switching) | ≤ 0.20 | 0.2982 | 0.2771 | −0.021 | FAIL | FAIL |
| Hamming (always-T) | ≤ 0.10 | 0.3273 | 0.2943 | −0.033 | FAIL | FAIL |
| Hamming (always-C) | ≤ 0.10 | 0.2005 | 0.2574 | +0.057 | FAIL | FAIL |
| ECE | ≤ 0.08 | 0.2790 | 0.2554 | −0.024 | FAIL | FAIL |
| RMSE on $\mu$ | ≤ 0.15 | 0.2765 | 0.2872 | +0.011 | FAIL | FAIL |
| RMSE on $P$ (Frob) | ≤ 0.20 | 0.1607 | 0.1604 | −0.000 | PASS | PASS |
| Multi-start fraction | ≥ 0.40 | 0.7883 | 0.7383 | −0.050 | PASS | PASS |
| Mean posterior entropy | ≤ 0.38 | 0.3025 | 0.3026 | +0.000 | PASS | PASS |

None of the five previously-failing metrics crossed into PASS. Hamming(T) improved by 0.033, Hamming(C) worsened by 0.057, and the cohort-averaged Hamming(switch) drifted by 0.021 in the right direction. ECE moved by 0.024 in the right direction. $\mu$-RMSE moved 0.011 in the wrong direction. $P$-RMSE, multi-start fraction, and posterior entropy are essentially unchanged.

## What v0.1 ruled out and what it confirmed

The action-availability calibration mismatch contributes approximately 0.02–0.05 of the Hamming gap on each cohort, in the directions predicted by per-slice nat-arithmetic before the run. The opposite-direction asymmetry between always-T (improved) and always-C (worsened) is the direct empirical signature of the discriminative-power calculation — KL distance between Bernoulli(0.4) and Bernoulli(0.2) is smaller than between Bernoulli(0.5) and Bernoulli(0.2), so calibrating the state-$T$ prior to truth helps the always-T cohort and hurts the always-C cohort by reducing inter-state contrast. The patch is doing exactly what the math predicts; the residual gap is therefore not calibration-attributable.

The structural-identification fingerprint persists intact across both runs: $\mu$-RMSE high (0.287), posterior entropy low (0.303), multi-start fraction high (0.738). EM is converging *confidently* and *consistently* to wrong emission means. The v0.1 experiment was the controlled trial; the result confirms the failure is structural identification, not calibration and not optimization.

## Recommended next actions

1. **v0.2 patch work should not proceed automatically.** The next session should be a diagnostic discussion with the human to scope the investigation, examine the v0.1 outputs for evidence of EM convergence pathologies, and decide whether the next experiment is a deeper harness rewrite or a re-examination of the §4.1 specification itself. The decision-tree branch for FAIL explicitly excludes automatic v0.2 staging precisely because a structural-identification fingerprint is not addressable by a single-line patch.

2. **The Layer 2 design document is not updated by this outcome.** The v0.2 design document's §11.2 limitations subsection already reports the v0 threshold-failure result honestly; the v0.1 result strengthens that subsection's framing but does not change its conclusion. A design-document update should wait until either the structural cause is identified and addressed (in which case §11.2 reports a positive validation result) or the v1 harness expansion supersedes v0/v0.1 entirely.

3. **The §4.3.6 expected-values table in the research document is the single most-suspect remaining hypothesis.** Two independent seeded runs of the §4.3.4 harness have now produced the same failure pattern on the same five metrics, and a controlled calibration patch has moved the metrics by exactly the predicted small amount without closing the gap. The simplest hypothesis remaining is that the §4.3.6 values were never verified against §4.3.4 code. The research document is immutable per the project's working rules, but a follow-up issue against the research-document maintainer is appropriate.

4. **Threads B (SEC-enforcement-labeled supervised pipeline), C (speaker-attributed Layer 4), D (cost-model calibration), and E (Layer 1 / Layer 2 integration) remain unblocked at the spec level.** The v0/v0.1 finding does not invalidate the §4 specification — those subsections describe a model with skew-normal narrative emissions, hierarchical Type-II ML, role-level pooling, and full multi-component action emission, none of which the v0 harness implements. Threads that consume the spec (not the harness) can proceed in parallel.

## Followups for human review

- **Most-actionable diagnostic, no rerun required.** Compare the per-cohort emission-mean RMSE against the per-cohort entropy and multi-start fraction in `outputs/results.json`. The v0.1 default-cell triple is (μ-RMSE = 0.287, entropy = 0.303, multistart = 0.738): RMSE is high *while* entropy is low and multi-start agreement is high. This triple is the structural-identification fingerprint. EM is converging confidently and consistently to a wrong answer; the issue is not optimization (which would show low multi-start agreement and high entropy from non-convergence), and it is not calibration (which the v0.1 patch ruled out). The most plausible remaining structural explanation is that EM with the current prior + initialization scheme cannot collapse onto a single component when cohort-truth data only supports one component, leaving $\hat\mu_T$ and $\hat\mu_C$ near each other instead of near (0.0, 0.4).

- **Suggested diagnostic experiments (not pre-staged; require human discussion before scope).** A focused sub-experiment on the always-T cohort with a 1-component versus 2-component fit comparison would test the cohort-collapse hypothesis directly. A separate sub-experiment varying the EB prior strength `V_prior` would test whether the prior is too strong or too weak relative to the data weight. A third sub-experiment instrumenting the diagnostics file (the JSONL the §4.3.5 spec calls for but the harness never writes) would surface per-executive identifiability flags and let us see whether failures concentrate in particular executives or are uniformly distributed.

- **Scope of the §4.3.6 follow-up.** The research-document maintainer should be asked specifically whether the §4.3.6 expected values were generated by the §4.3.4 code or by an earlier / different harness. If the answer is "earlier / different," the v0/v0.1 result is the verification step doing its job and the research document needs an erratum. If the answer is "the §4.3.4 code under different numpy / scipy versions," the v0.1 result still stands as evidence that the calibration row does not account for the gap. Either way, the §4.3.6 table cannot be treated as a load-bearing target until the discrepancy is resolved.

- **Cost-of-rerun for diagnostic experiments.** Each full-sweep run is ~20 minutes single-core. A cohort-only or cell-only run (always-T at the default cell, no robustness sweep) is ~75 seconds. The single-cohort-single-cell pattern is the right grain for diagnostic iteration; the full sweep should be reserved for milestone-level validation runs.
