# diagnose.py — v0.3 BETA_X_NULL inline diagnostic
#
# Per-executive identifiability data that run_vprior_sweep aggregates away.
# Imports em_one and gen_executive directly from run.py and re-implements
# only the cohort loop with augmented per-executive logging.
#
# Sweep configuration: V_prior=0.01, beta_sell=0.3, a_chan=0.6 (the v0.3
# default cell at the strongest prior anchor). 3 cohorts (T, C, switch),
# 60 executives per cohort, 10 multistarts per executive — same T_dist as
# run_vprior_sweep.
#
# Note on beta_x: em_one's `best` dict does not expose the converged
# beta_x, so we re-derive it post-hoc by running Newton iterations on
# the best-multistart log_gamma. At EM convergence, beta_x is a fixed
# point of the Newton update given log_gamma, so the re-derivation is
# exact modulo Newton's tolerance (1e-9 here).
#
# Single-command reproduction: python diagnose.py --seed 20260426
# Output: outputs/diag.json (180 per-executive records, ~150 s wall-clock).
# Dependencies: numpy>=1.24, scipy>=1.10 (same as run.py).

import argparse, json, os, time
import numpy as np
from scipy.special import expit

from run import em_one, gen_executive


def derive_beta_x(d, fit, max_iter=50, tol=1e-9):
    """Re-derive the converged covariate slope from the best multistart's
    converged gamma. Mirrors run.py's M-step Newton block exactly."""
    delta = d['delta']
    A_d = d['A_d']
    x = d['x']
    nu = fit['nu']
    gamma = np.exp(fit['log_gamma'])
    K = 2
    beta_x = 0.0
    y = (delta == -1).astype(float)
    for _ in range(max_iter):
        grad_beta = 0.0
        hess_beta = 0.0
        for k in range(K):
            w = gamma[:, k] * A_d
            if w.sum() < 1.0:
                continue
            p = expit(nu[k] + beta_x * x)
            grad_beta += w @ ((y - p) * x)
            hess_beta += -(w @ (p * (1 - p) * x * x)) - 1e-3
        if hess_beta < -1e-9:
            step = -grad_beta / hess_beta
            beta_x = beta_x + step
            if abs(step) < tol:
                break
        else:
            break
    return float(beta_x)


def run_diagnose(seed):
    rng = np.random.default_rng(seed)
    T_dist = lambda: int(np.clip(rng.lognormal(np.log(38), 0.7), 10, 200))
    beta_sell, a_chan = 0.3, 0.6
    V_prior = 0.01
    records = []
    for cohort, regime in [('T', 'T'), ('C', 'C'), ('switch', 'switch')]:
        for exec_idx in range(60):
            T_i = T_dist()
            d = gen_executive(rng, T_i, regime, beta_sell, a_chan)
            fit, diag = em_one(d, rng=rng, V_prior=V_prior)
            beta_x_conv = derive_beta_x(d, fit)
            log_gamma = fit['log_gamma']
            gamma_full = np.exp(log_gamma)
            z_hat = np.argmax(gamma_full, axis=1)
            rec = dict(
                exec_idx=exec_idx,
                cohort=cohort,
                T_i=int(T_i),
                z_true=d['z'].astype(int).tolist(),
                mu_T=float(fit['mu'][0]),
                mu_C=float(fit['mu'][1]),
                om_T=float(fit['om'][0]),
                om_C=float(fit['om'][1]),
                nu_T=float(fit['nu'][0]),
                nu_C=float(fit['nu'][1]),
                beta_x=beta_x_conv,
                xi_o_T=float(fit['xi_o'][0]),
                xi_o_C=float(fit['xi_o'][1]),
                log_pi=fit['log_pi'].tolist(),
                log_A=fit['log_A'].tolist(),
                label_swaps=int(diag['label_swaps']),
                multistart_winners=int(diag['multistart_winners']),
                z_hat=z_hat.astype(int).tolist(),
                per_slice_gamma_C=gamma_full[:, 1].tolist(),
            )
            records.append(rec)
    return records


def cohort_summary(records, cohort):
    """Quick console-only summary for the print at end-of-run; full data is
    in outputs/diag.json."""
    cr = [r for r in records if r['cohort'] == cohort]
    n = len(cr)
    label_swaps_rate = sum(r['label_swaps'] for r in cr) / (n * 10)
    multistart_mean = sum(r['multistart_winners'] for r in cr) / (n * 10)
    beta_x_mean = sum(r['beta_x'] for r in cr) / n
    beta_x_std = (sum((r['beta_x'] - beta_x_mean) ** 2 for r in cr) / n) ** 0.5
    # Per-executive Hamming after cohort-folding (same metric as run.py)
    hammings = []
    for r in cr:
        z_true = np.array(r['z_true'])
        z_hat = np.array(r['z_hat'])
        h0 = float(np.mean(z_hat != z_true))
        h1 = float(np.mean(z_hat != (1 - z_true)))
        hammings.append(min(h0, h1))
    h_mean = sum(hammings) / n
    h_med = sorted(hammings)[n // 2]
    h_min = min(hammings)
    h_max = max(hammings)
    h_q1 = sorted(hammings)[n // 4]
    h_q3 = sorted(hammings)[3 * n // 4]
    return dict(
        n=n,
        label_swaps_rate=label_swaps_rate,
        multistart_mean=multistart_mean,
        beta_x_mean=beta_x_mean,
        beta_x_std=beta_x_std,
        hamming_mean=h_mean,
        hamming_median=h_med,
        hamming_min=h_min,
        hamming_q1=h_q1,
        hamming_q3=h_q3,
        hamming_max=h_max,
    )


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--seed', type=int, default=20260426)
    p.add_argument('--out', type=str,
                   default=os.path.join(os.path.dirname(os.path.abspath(__file__)), 'outputs'))
    args = p.parse_args()
    os.makedirs(args.out, exist_ok=True)
    t0 = time.time()
    records = run_diagnose(args.seed)
    elapsed = time.time() - t0
    out = dict(
        seed=args.seed,
        V_prior=0.01,
        beta_sell=0.3,
        a_chan=0.6,
        elapsed_sec=elapsed,
        n_records=len(records),
        records=records,
    )
    out_path = os.path.join(args.out, 'diag.json')
    with open(out_path, 'w') as f:
        json.dump(out, f, indent=2, default=str)
    print(f'# v0.3 diagnostic — V_prior=0.01, beta_sell=0.3, a_chan=0.6')
    print(f'# seed={args.seed}, elapsed={elapsed:.1f}s, n_records={len(records)}')
    print(f'# output: {out_path}')
    print(f'')
    print(f'| cohort | n | label_swaps_rate | multistart_mean | beta_x mean ± sd | Hamming min | q1 | median | mean | q3 | max |')
    print(f'|---|---|---|---|---|---|---|---|---|---|---|')
    for cohort in ('T', 'C', 'switch'):
        s = cohort_summary(records, cohort)
        print(
            f"| {cohort} | {s['n']} | {s['label_swaps_rate']:.3f} | {s['multistart_mean']:.3f} | "
            f"{s['beta_x_mean']:+.3f} ± {s['beta_x_std']:.3f} | "
            f"{s['hamming_min']:.3f} | {s['hamming_q1']:.3f} | {s['hamming_median']:.3f} | "
            f"{s['hamming_mean']:.3f} | {s['hamming_q3']:.3f} | {s['hamming_max']:.3f} |"
        )


if __name__ == '__main__':
    main()
