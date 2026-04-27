# notes.md — `hmm_validation_v0_4`

## Patch

This is the diff between `experiments/layer_2/hmm_validation_v0_3/run.py` and `experiments/layer_2/hmm_validation_v0_4/run.py`. It is confined to one block deletion in `em_one`'s inner EM loop. The model code outside the deleted M-step block (the generator, `log_emissions`, `forward_backward`, the v0.3 β_x M-step, the V_prior sweep harness) is byte-identical to v0.3.

```diff
--- experiments/layer_2/hmm_validation_v0_3/run.py
+++ experiments/layer_2/hmm_validation_v0_4/run.py
@@ em_one inner loop, after the opportunistic logit M-step
             # opportunistic logit
             ...
                 xi_o[k] = xi_o[k] - grad/hess
-            # initial + transition (with Dirichlet prior)
-            log_pi = np.log(gamma[0] + 1e-9); log_pi -= logsumexp(log_pi)
-            n_jk = xi_.sum(axis=0)
-            n_jk[0, 0] += alpha_A[0]; n_jk[1, 1] += alpha_A[0]
-            n_jk[0, 1] += alpha_A[1]; n_jk[1, 0] += alpha_A[1]
-            A_new = n_jk / n_jk.sum(axis=1, keepdims=True)
-            log_A = np.log(A_new + 1e-9)
+            # initial state only (transitions frozen at canonical values; see README)
+            log_pi = np.log(gamma[0] + 1e-9); log_pi -= logsumexp(log_pi)
```

The five-line transition-matrix M-step block (`n_jk = xi_.sum(axis=0)` through `log_A = np.log(A_new + 1e-9)`) is deleted. The `log_pi` update for the initial state distribution is preserved (initial state is independent of the transition matrix). The comment is updated to reflect the new behaviour.

The `log_A` initialization at the top of the multistart loop — `log_A = np.log(np.array([[0.95, 0.05], [0.20, 0.80]]))` — is unchanged from v0.3. Combined with the M-step deletion, this means `log_A` retains its initialization value throughout every EM iteration of every multistart, regardless of cohort, regardless of V_prior. The transition matrix is frozen at the generator's canonical values.

## Hypothesis under test

If the v0.3 BETA_X_NULL outcome's residual Hamming(T) plateau is driven by the EM's inability to identify the transition matrix on always-T data — specifically the Dirichlet prior `alpha_A = (50.0, 5.0)` overweighting the C-row equilibrium at (0.091, 0.909) versus truth (0.20, 0.80), making phantom-C excursions sticky under forward-backward smoothing — then freezing A at the canonical `[[0.95, 0.05], [0.20, 0.80]]` should drop Hamming(T) at V_prior = 0.01 below 0.05.

The alternative is that the floor is deeper than transition-matrix identification. Reading (3) from the v0.3 BETA_X_NULL analysis — short-trace executives carry an inherent identifiability bound under weak forward-backward smoothing regardless of model parameters — would survive the v0.4 patch unchanged, since freezing A at truth still doesn't add data to short-trace executives, only fixes the smoothing prior.

## Reproducibility command

```
cd experiments/layer_2/hmm_validation_v0_4
pip install -r requirements.txt
python run.py --seed 20260426
```

Expected wall-clock: similar to v0.3's 796 s. The M-step block deletion saves a small amount of compute per outer iteration, but EM convergence trajectories may shift slightly. Estimate 750–800 s single-core.

## Outcome

The branch will be selected after the v0.4 run completes. The three subsections below correspond to the three branches of `decision_tree.md`.

### Outcome: TRANSITION_FLOOR_CONFIRMED

*To be populated after the run.*

Criterion: Hamming(T) at V_prior = 0.01 drops to below 0.05 under frozen-truth-A. The v0.3 plateau was the transition-matrix identification floor — the Dirichlet C-row asymmetric anchor was the load-bearing residual factor. v0.5 hierarchical pooling on transitions (per design document §4.1.2) is the right cure; the v0.5 Hamming target stays at the original ≤0.10 with confidence that hierarchical pooling on a population of executives (where some executives DO observe C→T transitions) provides the data the always-T cohort lacks individually.

### Outcome: TRANSITION_FLOOR_PARTIAL

*To be populated after the run.*

Criterion: Hamming(T) at V_prior = 0.01 drops by more than 0.10 (so transition-matrix identification is doing material work) but plateaus above 0.05. Transition-matrix identification accounts for most but not all of the v0.3 gap. v0.5 proceeds with the original target ≤0.10 but with one additional risk to track in STATUS.md: hierarchical pooling on transitions may not fully close Hamming(T), and a backup acceptance band of ≤0.15 may be needed. The most plausible residual cause is reading (3) — short-trace per-slice ambiguity — which hierarchical pooling on transitions does not fix.

### Outcome: TRANSITION_FLOOR_NULL

*To be populated after the run.*

Criterion: Hamming(T) at V_prior = 0.01 stays above 0.15 under frozen-truth-A. The plateau is deeper than transition-matrix identification. The half-day diagnostic discussion is now mandatory; reading (3) as irreducible-or-deeply-structural becomes the leading candidate for the v0.5 target revision. The metrics-side cohort-folding pathology and the per-executive Hamming distribution shape become the next targets for diagnostic work, possibly via instrumentation of the EM loop with per-iteration trajectory traces or via a reformulation of the metric to use Stephens KL on a 2-channel narrative emission (which the planned v0.5 design already includes).
