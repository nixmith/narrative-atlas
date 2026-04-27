# notes.md — `hmm_validation_v0_2`

## Patch

This is the diff between `experiments/layer_2/hmm_validation_v0_1/run.py` and `experiments/layer_2/hmm_validation_v0_2/run.py`. It is confined to the validation harness; the model code (`gen_executive`, `log_emissions`, `forward_backward`, `em_one`) is byte-identical to v0.1.

**Change 1 (confirmation, no code change).** `em_one` already accepts `V_prior` as a keyword argument with default `4.0`:

```python
def em_one(d, n_starts=10, n_iter=80, tol=1e-5, rng=None,
           mu_prior=(0.0, 0.4), V_prior=4.0, alpha_A=(50.0, 5.0)):
```

Confirmed. The signature is unchanged from v0.1. v0.2 simply exercises this knob from the harness.

**Change 2 (harness rewrite).** `run_sweep` and its companion `evaluate_thresholds` are removed. `run_vprior_sweep` is added in their place, and `main()` is updated to call `run_vprior_sweep(args.seed)` and write `outputs/results.md` as a `V_prior` × metrics table:

```diff
--- experiments/layer_2/hmm_validation_v0_1/run.py
+++ experiments/layer_2/hmm_validation_v0_2/run.py
@@
-def run_sweep(seed):
-    rng = np.random.default_rng(seed)
-    T_dist = lambda: int(np.clip(rng.lognormal(np.log(38), 0.7), 10, 200))
-    sweeps = []
-    for beta_sell in [0.0, 0.3, 0.6]:
-        for a_chan in [1.0, 0.6, 0.3]:
-            ...
-    return sweeps
-
-def evaluate_thresholds(sweeps):
-    ...
+def run_vprior_sweep(seed, vprior_values=(0.01, 0.1, 1.0, 4.0, 64.0)):
+    rng = np.random.default_rng(seed)
+    T_dist = lambda: int(np.clip(rng.lognormal(np.log(38), 0.7), 10, 200))
+    beta_sell, a_chan = 0.3, 0.6
+    results = []
+    for V_prior in vprior_values:
+        cohort_metrics = {}
+        for cohort, regime in [('T','T'), ('C','C'), ('switch','switch')]:
+            ...
+            for i in range(60):
+                ...
+                fit, diag = em_one(d, rng=rng, V_prior=V_prior)
+                ...
+        results.append(dict(V_prior=V_prior, **cohort_metrics))
+    return results

@@ def main():
-    sweeps = run_sweep(args.seed)
-    pf = evaluate_thresholds(sweeps)
+    results = run_vprior_sweep(args.seed)
     ...
-    out = dict(seed=args.seed, elapsed_sec=elapsed, sweeps=sweeps, pass_fail=pf)
+    # writes results.json (raw list-of-dicts) and results.md
+    # (rows = V_prior, columns = Hamming(switch), Hamming(T), Hamming(C), ECE, mu-RMSE, multistart, entropy)
```

The `(beta_sell, a_chan)` grid is collapsed to the single default cell `(0.3, 0.6)`. The pass/fail threshold table is removed because v0.2 is a diagnostic sweep, not a threshold-validation run; thresholds will be re-introduced at v0.5 when the actual identification test runs against an unbiased prior.

## Hypothesis

If the v0/v0.1 threshold-failure pattern reflects EM converging to a wrong local maximum that the default `V_prior = 4.0` Normal prior on `mu` cannot pull it out of, then shrinking `V_prior` should drop μ-RMSE toward zero and Hamming toward small values, while the convergence diagnostics drift only slightly. The expected directional pattern is monotone in `V_prior`: smaller `V_prior` means stronger anchor, means tighter recovery of `mu`, means cleaner state assignment.

A positive result confirms the structural-identification reading of the v0/v0.1 failure but does **not** validate the §4 specification. The prior mean equals the generator's true mean by construction (`mu_prior = (0.0, 0.4)`, generator emits `mu_T = 0.0, mu_C = 0.4`); a strongly anchored prior centred on truth produces a posterior centred on truth as a tautology of empirical Bayes. The actual identification test is v0.5.

## Reproducibility command

```
cd experiments/layer_2/hmm_validation_v0_2
pip install -r requirements.txt
python run.py --seed 20260426
```

Expected wall-clock: roughly 11–12 minutes single-core (5 `V_prior` values × 3 cohorts × 60 executives ≈ 900 EM fits, vs v0.1's ≈ 1620 EM fits at ≈ 20.7 minutes).

## Outcome

The branch will be selected after the v0.2 run completes. The three subsections below correspond to the three branches of `decision_tree.md`.

### Outcome: STRUCTURAL_CONFIRMED

*To be populated after the run.*

Criterion: μ-RMSE drops monotonically with `V_prior` toward roughly 0.02–0.05 at `V_prior = 0.01`; Hamming on each cohort drops in lockstep; multi-start fraction and posterior entropy drift only slightly. This matches the structural-identification hypothesis from v0.1 STATUS.md: a stronger prior anchor pulls EM out of the wrong local maximum it converges to under the weak default prior.

### Outcome: PARTIAL_CONFIRMED

*To be populated after the run.*

Criterion: μ-RMSE drops with `V_prior` but plateaus above ~0.10 even at `V_prior = 0.01`; **and / or** some metric (most likely Hamming(T) or ECE) remains anomalous in a direction the prior cannot fix. This indicates the prior strength is one contributing factor but not the only one — a second structural mismatch (most plausibly the missing `beta_x` slope update, or the cohort-folding metric masking a label-orientation issue) shares responsibility.

### Outcome: ANOMALOUS

*To be populated after the run.*

Criterion: μ-RMSE remains > 0.20 even at `V_prior = 0.01` despite the prior being centred on the generator's truth. This would be surprising — it implies the label-swap step or cohort-folding metric is masking a deeper issue, or the prior is being applied to the wrong quantity, or the EM update equations have a defect that prevents the prior from dominating even at extreme strength. Under this branch, v0.5 is deferred until the inference loop is debugged.
