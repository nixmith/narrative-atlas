# notes.md — `hmm_validation_v0_1`

## Patch

This is the single-line diff between `experiments/layer_2/hmm_validation_v0/run.py` and `experiments/layer_2/hmm_validation_v0_1/run.py`:

```diff
--- experiments/layer_2/hmm_validation_v0/run.py
+++ experiments/layer_2/hmm_validation_v0_1/run.py
@@ -66 +66 @@
-        p_present = expit(np.where(k == 0, 0.0, -1.4))  # state-dependent absence prior
+        p_present = expit(np.where(k == 0, np.log(0.4 / 0.6), np.log(0.2 / 0.8)))  # state-dependent absence prior, calibrated to generator
```

The new line evaluates to `p_present(T) = 0.40` and `p_present(C) = 0.20`, matching the generator's `Bernoulli(0.4)` and `Bernoulli(0.2)` action-availability draws exactly. No other line in `run.py` is changed; no other file in the experiment is changed.

## Hypothesis

If the action-availability prior mismatch is the proximate cause of the v0 threshold failures, calibrating the prior to match the generator should move all five failing metrics into PASS at the default sweep point.

## Reproducibility command

```
cd experiments/layer_2/hmm_validation_v0_1
pip install -r requirements.txt
python run.py --seed 20260426
```

Wall-clock observed in the user's environment: 1241.5 s (≈ 20.7 minutes single-core), comparable to v0's 1185.2 s.

## Outcome

The branch selected by the v0.1 run is **FAIL**. The PASS and PARTIAL PASS subsections below are intentionally left empty as a record of which branch was selected.

### Outcome: PASS

*Not selected.*

### Outcome: PARTIAL PASS

*Not selected.*

### Outcome: FAIL

The patched harness was executed against `--seed 20260426` and ran cleanly to completion in 1241.5 s. None of the five previously-failing metrics crossed into PASS. The hypothesis is rejected as the *proximate* cause of the v0 threshold failures. The patch's contribution to the gap is small relative to the gap and is consistent with the per-slice nat-arithmetic prediction (≈ 0.02 nats/slice of additional T-vs-C contrast on always-T data, with an opposite-direction reduction in always-C contrast).

#### Side-by-side comparison (default sweep cell, β_sell = 0.3, a_chan = 0.6)

| Metric | Threshold | v0 | v0.1 | Δ (v0.1 − v0) | v0 verdict | v0.1 verdict |
|---|---|---|---|---|---|---|
| Hamming (switching) | ≤ 0.20 | 0.2982 | 0.2771 | −0.021 | FAIL | FAIL |
| Hamming (always-T) | ≤ 0.10 | 0.3273 | 0.2943 | −0.033 | FAIL | FAIL |
| Hamming (always-C) | ≤ 0.10 | 0.2005 | 0.2574 | +0.057 | FAIL | FAIL |
| ECE | ≤ 0.08 | 0.2790 | 0.2554 | −0.024 | FAIL | FAIL |
| RMSE on $\mu$ | ≤ 0.15 | 0.2765 | 0.2872 | +0.011 | FAIL | FAIL |
| RMSE on $P$ (Frob) | ≤ 0.20 | 0.1607 | 0.1604 | −0.000 | PASS | PASS |
| Multi-start fraction | ≥ 0.40 | 0.7883 | 0.7383 | −0.050 | PASS | PASS |
| Mean posterior entropy | ≤ 0.38 | 0.3025 | 0.3026 | +0.000 | PASS | PASS |

#### Pre-run prediction vs observation

The pre-run prediction (recorded in chat before the v0.1 run completed) was that the patch would move metrics in specific directions by specific magnitudes. Every prediction matched the observed result qualitatively, and most matched quantitatively to within a factor of two. The asymmetry between always-T (which improved by 0.033) and always-C (which worsened by 0.057) is the direct empirical signature of the action-availability factor's discriminative-power calculation: KL distance between Bernoulli(0.4) and Bernoulli(0.2) is smaller than KL distance between Bernoulli(0.5) and Bernoulli(0.2), so calibrating the state-T prior to the truth makes the always-T cohort easier and the always-C cohort harder. The patch is doing exactly what the math predicts; the residual gap is therefore not calibration-attributable.

#### Sweep-grid pattern

Every cell in the v0.1 sweep grid moved by a similar small amount in the direction of the v0 cell. The robustness behaviour is unchanged at the relative level — Hamming(switch) under high $\beta_{\text{sell}}$ at $a_{\text{chan}} = 0.6$ is 0.245 (v0.1) vs 0.270 (v0); under low $a_{\text{chan}}$ it is 0.275 (v0.1) vs 0.286 (v0). The baseline shift of approximately 0.16 in Hamming relative to the §4.3.6 expected values persists in every cell.

#### What this rules out and what it confirms

The action-availability calibration mismatch contributes approximately 0.02–0.05 of the Hamming gap on each cohort, exactly as the pre-run nat-arithmetic predicted. It is not the proximate cause of the threshold failures. The remaining gap on every metric is 0.10–0.27 of Hamming, and the patch buys a small fraction of that.

The structural-identification fingerprint persists intact:
- $\mu$-RMSE remained at 0.287 (essentially unchanged from v0's 0.277)
- Posterior entropy unchanged at 0.303 (well below the 0.38 threshold)
- Multi-start fraction at 0.738 (still well above the 0.40 threshold)

EM is converging confidently, consistently, to wrong emission means. This is the signature of a structural identification problem, not an optimization problem and not a calibration problem. The v0.1 experiment is the controlled trial that confirms it.

#### What this means for downstream artifacts

The Layer 2 v0.2 design document is *not* updated by this outcome (per the FAIL branch of the decision tree). v0.2 patch work (the `beta_x` Newton update) is *not* automatically staged; the `beta_x` patch was the next-leading suspect in the v0 audit, but the structural-identification fingerprint suggests that no single-row patch is likely to close the gap. The next session is a diagnostic discussion before any further patch work.

The §4.3.6 expected-values table in the research document at `docs/layers/layer_2/research/Insider Divergence Detection as Bayesian HMM Spec with Covariate-Dependent Emission.md` is now strongly suspect. Two seeded runs of the §4.3.4 harness (v0 and v0.1) have failed it on the same five metrics by the same pattern; a controlled calibration patch has been shown to move the metrics by the predicted small amount without closing the gap. The simplest hypothesis remaining is that the §4.3.6 values were never verified against §4.3.4 code. This belongs in front of the research-document maintainer.

The Thread A specification (Layer 2 design doc §4) is not threatened by this outcome. The full §4 spec includes skew-normal narrative emissions, hierarchical Type-II ML, role-level pooling, and full multi-component action emission — all of which are absent from the v0 harness. The v0.1 finding tells us the simplified harness is failing because of a structural identification problem in the simplified model, not because the spec is wrong.
