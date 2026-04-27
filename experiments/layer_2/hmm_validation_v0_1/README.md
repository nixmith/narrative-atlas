# Layer 2 — HMM validation v0.1

This experiment is a single-line patch to `experiments/layer_2/hmm_validation_v0/run.py`. It tests one hypothesis: that the action-channel availability prior calibration mismatch identified as severity DEVIATION in `experiments/layer_2/hmm_validation_v0/audit.md` is the proximate cause of the v0 threshold failures reported in `experiments/layer_2/hmm_validation_v0/STATUS.md`.

The v0 directory is preserved as the immutable record of the first execution. v0.1 is a parallel experiment, not a replacement. Future patches (if any) become v0.2, v0.3, and so on under the same convention. Each patch tests exactly one hypothesis so that the diagnostic value of each run is preserved — applying multiple changes simultaneously would let us see whether the result improved but not which change accounted for the improvement.

## What v0.1 changes

A single line in the `log_emissions` function. The harness's hard-coded action-channel availability prior was set to $\sigma(0.0) = 0.50$ in state $T$ and $\sigma(-1.4) \approx 0.20$ in state $C$. The generator (`gen_executive`) draws action availability from `Bernoulli(0.4)` in state $T$ and `Bernoulli(0.2)` in state $C$. The state-$C$ calibration was already correct; the state-$T$ calibration was wrong by 10 percentage points. The patch replaces the hard-coded logits with `np.log(0.4 / 0.6)` and `np.log(0.2 / 0.8)`, which evaluate to logits whose sigmoid is exactly 0.40 and 0.20 respectively.

The patch is mathematically exact, not approximate, and is a one-line change. No other modification is made to `run.py`, the model logic, the parameter values, the threshold table, or the sweep grid.

## Single-command reproduction

```
cd experiments/layer_2/hmm_validation_v0_1
pip install -r requirements.txt
python run.py --seed 20260426
```

Wall-clock time is expected to match v0 at approximately 19.75 minutes single-core. The harness writes `outputs/results.json` and `outputs/results.md` in the same format as v0.

## Files in this directory

`run.py` is the harness with the single calibration patch applied. `requirements.txt` is identical to v0's. `notes.md` records the unified diff against v0, the hypothesis under test, the reproducibility command, and three empty subsections (`Outcome: PASS`, `Outcome: PARTIAL PASS`, `Outcome: FAIL`) that will be populated after the run completes. `decision_tree.md` is the runbook for the next round of work; it documents what gets updated in each of the three possible outcomes.

`STATUS.md` is intentionally not present until the run has completed and an outcome has been selected. The decision-tree branch determines which artifacts are updated and in what order.

## Relationship to the design document

The Layer 2 v0.2 design document (§11.2) cites the v0 harness and reports the v0 threshold-failure result honestly. The design document is not modified by the staging of v0.1 — only by the *outcome* of running v0.1, per the decision tree. If v0.1 passes, the design document is updated and bumped to v0.3. If v0.1 partial-passes, v0.2 is staged. If v0.1 fails, the design document is not updated and the next session is a diagnostic discussion.
