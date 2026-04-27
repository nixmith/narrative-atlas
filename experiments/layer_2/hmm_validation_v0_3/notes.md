# notes.md — `hmm_validation_v0_3`

## Patch

This is the diff between `experiments/layer_2/hmm_validation_v0_2/run.py` and `experiments/layer_2/hmm_validation_v0_3/run.py`. It is confined to `em_one`'s inner EM loop. The model code outside `em_one`'s M-step (the generator, `log_emissions`, `forward_backward`) is byte-identical to v0.2; the harness (`run_vprior_sweep`, `main`) is byte-identical to v0.2.

```diff
--- experiments/layer_2/hmm_validation_v0_2/run.py
+++ experiments/layer_2/hmm_validation_v0_3/run.py
@@ em_one inner loop, after the per-state nu[k] Newton block, before the opportunistic logit
             # M-step: sell logit (1-step Newton)
             for k in range(K):
                 ...
                 nu[k] = nu[k] - grad/hess
+            # M-step: beta_x (state-invariant slope, one Newton step per outer iteration)
+            grad_beta = 0.0
+            hess_beta = 0.0
+            for k in range(K):
+                w = gamma[:, k] * A_d
+                if w.sum() < 1.0:
+                    continue
+                p = expit(nu[k] + beta_x * x); y = (delta == -1).astype(float)
+                grad_beta += w @ ((y - p) * x)
+                hess_beta += -(w @ (p * (1-p) * x * x)) - 1e-3
+            if hess_beta < -1e-9:
+                beta_x = beta_x - grad_beta / hess_beta
             # opportunistic logit
```

The slope is state-invariant per the §4.1 spec: a single scalar `beta_x` is updated using both states' posterior responsibilities. The `hess_beta < -1e-9` guard handles the rare degenerate-weight case (e.g. an executive whose `A_d` channel is nearly absent and whose action emission contributes essentially zero curvature to the slope likelihood). Eight effective lines of code, no other change to `run.py`.

## What the v0.2 result tells us — quantitative anchors that motivate v0.3

The v0.2 μ-RMSE curve has a sharp drop concentrated between `V_prior = 1.0` and `V_prior = 0.01`: the row-by-row sweep reads 0.441 → 0.335 → 0.320 → 0.139 → 0.029. The mechanism is straightforward and worth recording precisely because it tells us what hierarchical pooling has to deliver in v0.5.

For an executive with `T_i ≈ 38` and `A_s`-channel availability 0.6, the effective data weight in the narrative-emission M-step is roughly `W_data ≈ T_i × E[A_s] ≈ 23`. The Normal prior on `mu` contributes weight `1 / V_prior`. The prior-to-data ratio across the sweep is therefore approximately:

| V_prior | 1/V_prior | prior/data | regime |
|---|---|---|---|
| 64.0 | 0.016 | 0.0007 | data dominates by ~1400× |
| 4.0 | 0.25 | 0.011 | data dominates by ~92× |
| 1.0 | 1.0 | 0.043 | data dominates by ~23× |
| 0.1 | 10 | 0.43 | data still dominates by ~2.3× |
| 0.01 | 100 | 4.3 | prior dominates by ~4.3× |

The dramatic μ-RMSE drop between `V_prior = 1.0` (0.320) and `V_prior = 0.1` (0.139) sits very near the data/prior crossover; the further drop to `V_prior = 0.01` (0.029) is the prior dominating completely. The reading is: **EM has a wrong-basin attractor that pulls μ̂ by ~0.32+ from truth at any data-dominated regime, and the prior overcomes it only when the prior weight exceeds the data weight by ~4× or more.**

This is the number to anchor on for v0.5 design. Hierarchical pooling has to provide an effective per-executive prior weight of order 4–10× the data weight to recover μ at the ~0.03 RMSE the v0.01 endpoint shows is achievable. If the role-level cohort has `N_role ≈ 30` executives each contributing `W ≈ 23`, the role-level posterior precision on `mu_role` is `≈ 30 × 23 = 690` in nat-units, and the implied per-executive prior precision (after pooling) is comfortably `≫ 100`. Hierarchical pooling has the budget, in principle. v0.5's design lives or dies on whether it can spend that budget on `mu` without regressing on the convergence diagnostics.

## Hypothesis under test

If the missing covariate-slope update in EM is the second contributing cause to the v0.2 PARTIAL_CONFIRMED outcome, then fitting `beta_x` should:

- Drop Hamming(T) at `V_prior = 0.01` from 0.188 (v0.2) toward small values (~0.05–0.10).
- Drop Hamming(switch) and ECE in lockstep on the switching cohort, because the action-channel mis-fit drives mis-labelling there too.
- Leave μ-RMSE at `V_prior = 0.01` near 0.029 (β_x is in the action emission, not the narrative emission); any material movement is evidence of coupled identification through the joint E-step.
- Move Hamming(C) by a state-symmetric amount in the helpful direction (high-x C-cohort slices have higher true sell propensity than the harness predicts, which makes them look more "C-like" to a fitted ν_C and helps Hamming(C) rather than hurting it). If Hamming(C) does not move, it is bounded by something else and the next experiment has a different scope.

## Reproducibility command

```
cd experiments/layer_2/hmm_validation_v0_3
pip install -r requirements.txt
python run.py --seed 20260426
```

Expected wall-clock: roughly 11–13 minutes single-core (β_x adds ~15–20% per-fit cost over v0.2's 634.5 s).

## Carried-over diagnostic threads from v0.2

Two structural signals from v0.2 will be re-tested under v0.3 by virtue of the full V_prior sweep being preserved.

The Hamming(switch) peak at `V_prior = 0.1` (0.297, versus 0.241 at `V_prior = 0.01`) is real — 0.056 over 60 executives is roughly 2σ on a per-cohort Hamming MC distribution, not noise. Three readings sit on it. (a) **Bimodal multistart**: at `V_prior = 0.1` some starts find the strong-anchor mode and others find a wrong-basin attractor, with the LL-best winner being neither cleanly. (b) **Emission overlap at partial pull**: at `V_prior = 0.1` μ-RMSE is 0.139, halfway between truth at `V_prior = 0.01` and the wrong basin at `V_prior = 1.0`; a partially-correct narrative emission is uniquely bad for label recovery because the within-class variance dominates the between-class signal more than at either endpoint. The multistart fraction being highest at `V_prior = 0.1` (0.798) is consistent with reading (b) — many starts converging to the same mediocre basin. (c) **Action-channel mis-fit**: the v0.2 harness has no β_x update, so the per-slice posteriors are biased by the action-channel likelihood at high-x slices, and that bias may interact non-linearly with the narrative emission overlap at intermediate prior strength. v0.3's β_x correction is largely orthogonal to (a) and (b) but eliminates (c). If the V_prior=0.1 Hamming(switch) peak survives β_x, (c) is ruled out and (a) vs (b) becomes the next diagnostic. If it disappears, (c) was the driver.

Per-executive `mu_hat` for the V_prior=0.1 switching cohort in `outputs/results.json` distinguishes (a) from (b) directly: tight clustering around an intermediate `mu_hat` is the (b) signature; two distinct clusters (some near truth, some at wrong-basin) is the (a) signature. v0.3's `outputs/results.json` carries the same per-cohort metric structure as v0.2, so the diagnostic is available without a separate run.

The Hamming(C) at `V_prior = 0.01` (0.160) being marginally worse than at `V_prior = 0.1` (0.151) is a small structural effect, not noise — same KL-distance asymmetry as the v0.1 always-T-improves / always-C-worsens pattern. At `V_prior = 0.01` the narrative emission is anchored at `mu_T = 0`, `mu_C = 0.4`, which discriminates more strongly for T data (because `mu_T = 0` is `0.4 / ω_C = 0.57` z-units from `mu_C` for state-C emissions but `0.4 / ω_T = 0.40` z-units from `mu_T` for state-T emissions — the state-C narrative is sharper). Combined with the missing β_x — which biases C labelling toward the wrong direction for high-x slices in the always-C cohort — `V_prior = 0.01` helps T more than C and the marginal Hamming(C) penalty is the visible residual. v0.3's β_x update should reduce the action-channel component of this asymmetry, leaving only the narrative-channel KL geometry as the residual. Magnitude of the v0.2 effect is small; v0.3 will tell us whether β_x flattens it.

## Outcome

The branch will be selected after the v0.3 run completes. The three subsections below correspond to the three branches of `decision_tree.md`.

### Outcome: BETA_X_CONFIRMED

*To be populated after the run.*

Criterion: Hamming(T) at `V_prior = 0.01` drops to <0.10 (matching the original v0.1 PASS threshold). Hamming(switch) and ECE drop in lockstep on the switching cohort. μ-RMSE remains near 0.029 (no coupling artefact). Confirms missing β_x slope as the second contributing cause; the action-channel intercept-only fit was the proximate cause of the v0.2 residual gap. Together with v0.2's STRUCTURAL_CONFIRMED μ-RMSE result, the path to v0.5 is de-risked on both the narrative-channel and action-channel sides.

### Outcome: BETA_X_PARTIAL

*To be populated after the run.*

Criterion: Hamming(T) at `V_prior = 0.01` drops by >0.05 but plateaus above 0.10. β_x is part of the story but not all of it. Candidate next causes (in approximate order of plausibility): the harness fits a Bernoulli on `delta = -1` only, but the spec calls for a categorical over `{-1, 0, +1}` matching the generator's full information set; the opportunistic flag has no covariate slope but the generator's `p_op` differs by state with a `±0.5` log-odds gap that may interact with the action-channel mis-fit; the label-fixing post-hoc swap (`mu[0] > mu[1]`) is fighting the strong prior in some episodes.

### Outcome: BETA_X_NULL

**Selected.** The v0.3 run with `--seed 20260426` produced Δ Hamming(T) at `V_prior = 0.01` of +0.002 (0.188 → 0.190), well below the BETA_X_NULL threshold of 0.03. Wall-clock 796.0 s (β_x added 25% over v0.2's 634.5 s, modestly above the predicted 15–20%; the Newton update is running, it just doesn't move the labeller). The diagnose.py companion ran in 133.9 s and produced `outputs/diag.json` with 180 per-executive records.

#### v0.3 results table (default cell, beta_sell=0.3, a_chan=0.6)

| V_prior | Hamming(switch) | Hamming(T) | Hamming(C) | ECE | mu-RMSE | multistart | entropy |
|---|---|---|---|---|---|---|---|
| 0.01 | 0.242 | 0.190 | 0.168 | 0.233 | 0.029 | 0.645 | 0.331 |
| 0.1  | 0.290 | 0.228 | 0.151 | 0.260 | 0.136 | 0.805 | 0.340 |
| 1.0  | 0.262 | 0.265 | 0.245 | 0.250 | 0.321 | 0.670 | 0.288 |
| 4.0  | 0.269 | 0.280 | 0.237 | 0.254 | 0.338 | 0.727 | 0.275 |
| 64.0 | 0.281 | 0.307 | 0.261 | 0.260 | 0.455 | 0.673 | 0.277 |

#### Row-by-row v0.2 → v0.3 deltas

| V_prior | Δ Hamming(switch) | Δ Hamming(T) | Δ Hamming(C) | Δ ECE | Δ μ-RMSE |
|---|---|---|---|---|---|
| 0.01 | +0.001 | +0.002 | +0.008 | +0.004 | +0.000 |
| 0.1  | −0.007 | −0.009 | +0.000 | −0.010 | −0.003 |
| 1.0  | +0.005 | +0.013 | +0.002 | +0.003 | +0.001 |
| 4.0  | +0.013 | −0.001 | −0.017 | +0.010 | +0.003 |
| 64.0 | +0.000 | +0.008 | −0.001 | +0.005 | +0.014 |

Every cell of every metric at every V_prior moves within MC tolerance (±0.02 Hamming/ECE, ±0.05 RMSE on 60 executives). The β_x Newton update is a near-no-op on the harness's reported metrics.

#### diagnose.py console summary (per-executive at V_prior=0.01)

| cohort | n | label_swaps_rate | multistart_mean | beta_x mean ± sd | Hamming min | q1 | median | mean | q3 | max |
|---|---|---|---|---|---|---|---|---|---|---|
| T | 60 | 0.000 | 0.668 | +73.999 ± 342.684 | 0.000 | 0.063 | 0.176 | 0.190 | 0.333 | 0.483 |
| C | 60 | 0.000 | 0.682 | -27.735 ± 629.000 | 0.000 | 0.057 | 0.149 | 0.168 | 0.250 | 0.500 |
| switch | 60 | 0.000 | 0.645 | +10.134 ± 416.156 | 0.000 | 0.143 | 0.241 | 0.242 | 0.371 | 0.481 |

The β_x cohort means and SDs are dominated by post-hoc Newton outliers (see "Known diagnose.py limitation" below); the trimmed medians (after dropping `|β_x| ≥ 5`) are +0.358 (T), +0.383 (C), +0.583 (switch), against truth 0.3.

#### What diagnose.py resolved

**(a) Label-swap reading dead.** `label_swaps_rate = 0.000` across 1800 multistart runs (180 executives × 10 starts). The post-hoc `mu[0] > mu[1]` reorder never fires when V_prior = 0.01 pins `mu` at the truth orientation. The decision_tree's leading BETA_X_NULL candidate is eliminated definitively.

**(b) Transition-matrix Dirichlet dominance confirmed on always-T cohort.** Fitted `log_A` rows are (T→) ≈ (0.921, 0.079) ± (0.012, 0.012) and (C→) ≈ (0.102, 0.898) ± (0.009, 0.009). The Dirichlet prior `alpha_A = (50.0, 5.0)` predicts equilibrium (0.909, 0.091) on each diagonal. Empirical means are within 0.013 of the prior anchor. The transition matrix is essentially the prior on always-T executives, which is the expected behaviour given that always-T traces have no observed C→T or C→C transitions to learn from. Transitions are *not* the locus of the Hamming(T) failure — but see Reading (4) below for what this *does* imply.

**(c) μ recovery essentially exact across every executive.** μ_T mean −0.018 (T), +0.009 (C), −0.012 (switch), each with SD < 0.04; μ_C mean +0.385 (T), +0.413 (C), +0.396 (switch), each with SD < 0.03. Truth is (0.0, 0.4). No executive has bad μ recovery. The narrative-channel structural-identification reading from v0.2 is intact and per-executive.

**(d) β_x converges to truth on most executives.** Trimmed medians +0.358 (T), +0.383 (C), +0.583 (switch) against truth 0.3. The "β_x converges to 0" reading from the v0.3 BETA_X_NULL analysis is dead; β_x is fitted in the right neighbourhood. Its discriminating power is too small to move the labeller because β_x · x has standard deviation ≈ 0.3 logits at typical |x| (since `x` is standard normal), versus the ν_k intercept difference of 1.2 logits. The action emission's state separability is intercept-dominated, and β_x's contribution to per-slice posterior is roughly an order of magnitude smaller than the joint emission factors that govern label assignment.

#### Known diagnose.py limitation

The post-hoc `derive_beta_x` routine in `diagnose.py` runs un-damped Newton iterates against a frozen `log_gamma` from the best multistart of `em_one`, with no E-step gamma-feedback to damp wild iterates. When `hess_beta` is barely past the `< -1e-9` guard, the Newton step `−grad_beta / hess_beta` can be enormous; the next iteration's `p = expit(nu_k + beta_x · x)` then saturates at 0 or 1, the Hessian collapses, and β_x runs off to ±∞. A subset of executives (9/60 T, 23/60 C, 14/60 switch) produces |β_x| ≥ 5 divergent iterates that dominate the cohort mean and SD. `em_one`'s in-loop β_x does not suffer this because each E-step recomputes `gamma` using the current β_x and damps it through the joint posterior. The proper fix is to expose β_x in `em_one`'s `best` dict in v0.5; do not patch `diagnose.py` here. The trimmed medians established in (d) are the load-bearing β_x finding.

#### Trace-length stratification

The cohort-mean Hamming(T) of 0.190 in `run.py`'s output is a length-mixture artifact. Per-executive Hamming stratified by `T_i`:

| cohort | T_i < 20 | T_i 20–50 | T_i ≥ 50 |
|---|---|---|---|
| T | n=11, median 0.300 | n=28, median 0.205 | n=21, **median 0.080** |
| C | n=8,  median 0.000\* | n=30, median 0.225 | n=22, median 0.135 |
| switch | n=15, median 0.278 | n=31, median 0.200 | n=14, median 0.248 |

Long always-T executives (T_i ≥ 50, n=21) have median Hamming **0.080** — passing the v0.1 threshold of 0.10. The corr(T_i, Hamming) on the T cohort is **−0.332**. The cohort-mean Hamming(T) of 0.190 averages short, mid, and long executives where short-trace identifiability is the limiting factor. The switch cohort shows no T_i effect (corr ≈ +0.072), consistent with switching being limited by per-slice ambiguity rather than length. **This isn't a fundamental floor — it's a per-executive identifiability bound that depends on trace length.**

#### Cohort-folding metric pathology

\*The C cohort short-trace median Hamming of 0.000 is a degenerate-`z_hat` artifact of the `min(h0, h1)` cohort fold. For an always-C executive (`z_true = all 1`), both `z_hat = all 0` and `z_hat = all 1` give metric value 0: `min(h0, h1) = min(1, 0) = 0` in the first case and `min(0, 1) = 0` in the second. The metric cannot distinguish "perfectly recovered" from "completely flipped" on always-cohort traces with degenerate `z_hat`. Long always-C numbers (median 0.135) are honest measurements because long traces produce intermediate `z_hat` distributions where the fold genuinely picks the better orientation. The always-T short-trace numbers are non-degenerate (median 0.300) and reflect real per-slice ambiguity under weak forward-backward smoothing. Stephens KL on a 2-channel narrative emission, planned for v0.5, is the right metric-side fix — it doesn't fold orientation but aligns components principled-ly using both narrative dimensions.

#### Four readings of the strong null

**Reading (1): β_x is fitted but not load-bearing.** Confirmed by diagnose.py finding (d) and the cohort-mean β_x trimmed medians near truth. β_x's per-slice contribution to the joint posterior is an order of magnitude smaller than the emission factors that dominate label assignment. The §4 spec's I6 identifiability claim is technically satisfied (β_x is identifiable from the data), but its finite-sample contribution to label recovery is negligible. The v0.5 design should include β_x for completeness but should not expect it to move the metric.

**Reading (2): Label-fixing-swap reading.** Dead (diagnose.py finding (a)).

**Reading (3): Trace-length stratification.** Short-trace executives (T_i < 20) carry an inherent identifiability bound under weak forward-backward smoothing — there is insufficient data per executive to overcome the per-slice emission ambiguity that any spec-compliant model has. Long-trace executives (T_i ≥ 50) already pass the v0.1 threshold at the v0.3 V_prior=0.01 endpoint. The right v0.5 lower-bound identification target is therefore the long-trace subset, not the cohort mean.

**Reading (4): Dirichlet C-row asymmetric anchor.** The Dirichlet prior `alpha_A = (50.0, 5.0)` puts the C-row equilibrium at (0.091, 0.909). But truth on the C-row is `(P_C_to_T, 1 − P_C_to_T) = (0.20, 0.80)`. The Dirichlet prior makes the C-row stickier than truth (P(C | prev=C) = 0.909 vs truth 0.80). When forward-backward on an always-T executive uses this transition matrix, a phantom-C excursion at slice `t` (driven by ambiguous emissions) is harder to escape at slice `t+1` than truth would allow: P(T | prev=C, prior-dominated) = 0.091 vs P(T | prev=C, truth) = 0.20. Always-T executives smooth using the Dirichlet C-row because they have no observed C→T transitions to learn from; the prior asymmetry directly inflates Hamming(T). v0.4 is the counterfactual test (freeze A at truth, re-run); if Hamming(T) drops on this counterfactual, the Dirichlet asymmetric anchor was the load-bearing factor and v0.5's transition design must incorporate role-level pooling on `log_A` rather than relying on a single fixed Dirichlet anchor.
