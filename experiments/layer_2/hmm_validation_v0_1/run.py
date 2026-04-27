# layer2_validate.py
# Layer 2 §4 synthetic-data validation harness, Thread A.
# Single-command reproduction: python layer2_validate.py --seed 20260426
# Dependencies: numpy>=1.24, scipy>=1.10 (no other libraries; from-scratch HMM).

import argparse, json, os, sys, time, hashlib
import numpy as np
from scipy.special import logsumexp, expit
from scipy.optimize import linear_sum_assignment

# -------- Generator --------------------------------------------------------

def gen_executive(rng, T, regime, beta_sell, a_channel,
                  mu_T=0.0, mu_C=0.4, om_T=1.0, om_C=0.7,
                  pi_init=(0.7, 0.3), P_T_to_C=0.05, P_C_to_T=0.20):
    # Latent path
    z = np.empty(T, dtype=int)
    if regime == 'T':
        z[:] = 0
    elif regime == 'C':
        z[:] = 1
    else:
        z[0] = rng.choice(2, p=pi_init)
        for t in range(1, T):
            p = P_T_to_C if z[t-1] == 0 else (1 - P_C_to_T)
            z[t] = rng.choice(2, p=[1-p, p]) if z[t-1] == 0 else rng.choice(2, p=[P_C_to_T, 1-P_C_to_T])
    # Covariate: rolling 26w firm return
    x = rng.standard_normal(T)
    # Narrative emission: skew-normal approximated as Gaussian for tractability
    mu_z = np.where(z == 0, mu_T, mu_C)
    om_z = np.where(z == 0, om_T, om_C)
    s = mu_z + om_z * rng.standard_normal(T)
    # Action-direction emission: state-dependent + mechanical price coupling
    p_sell = expit(np.where(z == 0, -0.6, 0.6) + beta_sell * x)
    delta = np.where(rng.uniform(size=T) < p_sell, -1, 0)
    # Opportunistic flag
    p_op = np.where(z == 0, 0.25, 0.75)
    o = (rng.uniform(size=T) < p_op).astype(int)
    # Channel availability
    A_s = (rng.uniform(size=T) < a_channel).astype(int)
    A_d = (rng.uniform(size=T) < np.where(z == 0, 0.4, 0.2)).astype(int)  # informative absence
    return dict(z=z, x=x, s=s, delta=delta, o=o, A_s=A_s, A_d=A_d, T=T, regime=regime)

# -------- Log-space forward-backward --------------------------------------

def log_emissions(s, delta, o, A_s, A_d, x, mu, om, nu, xi_o, beta_x):
    # mu, om: (K,), state-conditional narrative mean and SD
    # nu: (K,), state-conditional sell-logit intercept
    # xi_o: (K,), opportunistic-flag logit intercept
    # beta_x: scalar, slope of sell logit on covariate
    T_ = s.shape[0]; K = mu.shape[0]
    log_e = np.zeros((T_, K))
    for k in range(K):
        # narrative (Gaussian); contributes only when A_s == 1
        ll_s = -0.5*(np.log(2*np.pi*om[k]**2) + (s - mu[k])**2 / om[k]**2)
        log_e[:, k] += A_s * ll_s
        # action direction (Bernoulli on sell)
        p_sell = expit(nu[k] + beta_x * x)
        ll_d = np.where(delta == -1, np.log(p_sell + 1e-300), np.log(1 - p_sell + 1e-300))
        log_e[:, k] += A_d * ll_d
        # opportunistic flag emission (Bernoulli)
        p_o = expit(xi_o[k])
        ll_o = np.where(o == 1, np.log(p_o + 1e-300), np.log(1 - p_o + 1e-300))
        log_e[:, k] += A_d * ll_o
        # informative-absence factor on action channel
        p_present = expit(np.where(k == 0, np.log(0.4 / 0.6), np.log(0.2 / 0.8)))  # state-dependent absence prior, calibrated to generator
        ll_a = np.where(A_d == 1, np.log(p_present), np.log(1 - p_present))
        log_e[:, k] += ll_a
    return log_e

def forward_backward(log_e, log_pi, log_A):
    T_, K = log_e.shape
    log_alpha = np.full((T_, K), -np.inf)
    log_alpha[0] = log_pi + log_e[0]
    for t in range(1, T_):
        log_alpha[t] = logsumexp(log_alpha[t-1][:, None] + log_A, axis=0) + log_e[t]
    log_beta = np.zeros((T_, K))
    for t in range(T_-2, -1, -1):
        log_beta[t] = logsumexp(log_A + log_e[t+1][None, :] + log_beta[t+1][None, :], axis=1)
    loglik = logsumexp(log_alpha[T_-1])
    log_gamma = log_alpha + log_beta - loglik
    log_xi = (log_alpha[:-1, :, None] + log_A[None, :, :] +
              log_e[1:, None, :] + log_beta[1:, None, :] - loglik)
    return loglik, log_gamma, log_xi

# -------- EM for one executive --------------------------------------------

def em_one(d, n_starts=10, n_iter=80, tol=1e-5, rng=None,
           mu_prior=(0.0, 0.4), V_prior=4.0, alpha_A=(50.0, 5.0)):
    s, delta, o = d['s'], d['delta'], d['o']
    A_s, A_d = d['A_s'], d['A_d']
    x = d['x']; T_ = s.size; K = 2
    best = None
    diag = dict(ll_curves=[], converged_lls=[], entropies=[], hellingers=[],
                multistart_winners=0, label_swaps=0)
    for r in range(n_starts):
        # Initialize
        if r < 4:
            # k-means seeded
            idx = rng.choice(T_, size=K, replace=False)
            mu = np.sort(s[idx])
        elif r < 8:
            # random posterior
            z0 = rng.integers(0, 2, T_)
            mu = np.array([s[z0==k].mean() if (z0==k).any() else rng.standard_normal()
                           for k in range(K)])
            mu = np.sort(mu)
        else:
            mu = np.sort(rng.uniform(s.min(), s.max(), size=K))
        om = np.array([max(s.std(), 0.1)]*K)
        nu = np.array([-0.6, 0.6]) + 0.1*rng.standard_normal(K)
        xi_o = np.array([-1.0, 1.0]) + 0.1*rng.standard_normal(K)
        beta_x = 0.0
        log_pi = np.log(np.array([0.7, 0.3]))
        log_A = np.log(np.array([[0.95, 0.05], [0.20, 0.80]]))
        ll_curve = []
        prev_ll = -np.inf
        for it in range(n_iter):
            log_e = log_emissions(s, delta, o, A_s, A_d, x, mu, om, nu, xi_o, beta_x)
            ll, log_gamma, log_xi = forward_backward(log_e, log_pi, log_A)
            ll_curve.append(ll)
            if abs(ll - prev_ll) < tol * max(abs(ll), 1.0):
                break
            prev_ll = ll
            gamma = np.exp(log_gamma); xi_ = np.exp(log_xi)
            # M-step: emission means with Normal prior shrinkage to mu_prior
            for k in range(K):
                w = gamma[:, k] * A_s
                W = w.sum() + 1.0/V_prior
                mu[k] = (w @ s + mu_prior[k]/V_prior) / W
                resid = s - mu[k]
                om[k] = np.sqrt(max((w @ resid**2) / (gamma[:, k] @ A_s + 1e-9), 0.05))
            # M-step: sell logit (1-step Newton)
            for k in range(K):
                w = gamma[:, k] * A_d
                if w.sum() < 1.0:
                    continue
                p = expit(nu[k] + beta_x * x); y = (delta == -1).astype(float)
                grad = w @ (y - p)
                hess = -(w @ (p * (1-p))) - 1e-3
                nu[k] = nu[k] - grad/hess
            # opportunistic logit
            for k in range(K):
                w = gamma[:, k] * A_d
                if w.sum() < 1.0:
                    continue
                p = expit(xi_o[k]); y = o.astype(float)
                grad = w @ (y - p) - xi_o[k]/V_prior
                hess = -(w.sum() * p * (1-p)) - 1.0/V_prior  # p is scalar; numpy>=2 disallows w @ scalar
                xi_o[k] = xi_o[k] - grad/hess
            # initial + transition (with Dirichlet prior)
            log_pi = np.log(gamma[0] + 1e-9); log_pi -= logsumexp(log_pi)
            n_jk = xi_.sum(axis=0)
            n_jk[0, 0] += alpha_A[0]; n_jk[1, 1] += alpha_A[0]
            n_jk[0, 1] += alpha_A[1]; n_jk[1, 0] += alpha_A[1]
            A_new = n_jk / n_jk.sum(axis=1, keepdims=True)
            log_A = np.log(A_new + 1e-9)
        # Apply label-fixing constraint mu_T < mu_C; record label swaps
        swapped = mu[0] > mu[1]
        if swapped:
            mu = mu[::-1]; om = om[::-1]; nu = nu[::-1]; xi_o = xi_o[::-1]
            log_pi = log_pi[::-1]
            log_A = log_A[::-1, ::-1]
            log_gamma = log_gamma[:, ::-1]
            diag['label_swaps'] += 1
        diag['ll_curves'].append(ll_curve)
        diag['converged_lls'].append(ll)
        ent = float(-(np.exp(log_gamma) * log_gamma).sum() / T_)
        diag['entropies'].append(ent)
        # Hellinger between Gaussian narrative emissions
        h = np.sqrt(1 - np.sqrt(2*om[0]*om[1]/(om[0]**2+om[1]**2)) *
                    np.exp(-0.25*(mu[0]-mu[1])**2/(om[0]**2+om[1]**2)))
        diag['hellingers'].append(float(h))
        if best is None or ll > best['ll']:
            best = dict(ll=ll, mu=mu.copy(), om=om.copy(), nu=nu.copy(),
                        xi_o=xi_o.copy(), log_pi=log_pi.copy(), log_A=log_A.copy(),
                        log_gamma=log_gamma.copy())
    diag['multistart_winners'] = int(np.sum(np.array(diag['converged_lls']) >
                                             best['ll'] - 1e-3 * abs(best['ll'])))
    return best, diag

# -------- Validation harness ----------------------------------------------

def run_sweep(seed):
    rng = np.random.default_rng(seed)
    T_dist = lambda: int(np.clip(rng.lognormal(np.log(38), 0.7), 10, 200))
    sweeps = []
    for beta_sell in [0.0, 0.3, 0.6]:
        for a_chan in [1.0, 0.6, 0.3]:
            cohort_results = {}
            for cohort, regime in [('T', 'T'), ('C', 'C'), ('switch', 'switch')]:
                metrics_h = []; metrics_e = []; metrics_mu = []; metrics_P = []
                ms_winners = []; entropies = []; hellingers = []
                # sample 60 executives per cohort
                for i in range(60):
                    T_i = T_dist()
                    d = gen_executive(rng, T_i, regime, beta_sell, a_chan)
                    fit, diag = em_one(d, rng=rng)
                    z_hat = np.argmax(np.exp(fit['log_gamma']), axis=1)
                    # For always-T or always-C, fold both label orientations
                    h0 = np.mean(z_hat != d['z'])
                    h1 = np.mean(z_hat != (1 - d['z']))
                    h = min(h0, h1)
                    metrics_h.append(h)
                    # ECE on switching only
                    if cohort == 'switch':
                        gamma_C = np.exp(fit['log_gamma'])[:, 1]
                        # align if needed
                        if h1 < h0: gamma_C = 1 - gamma_C
                        bins = np.linspace(0, 1, 11)
                        idx = np.clip(np.digitize(gamma_C, bins) - 1, 0, 9)
                        ece = 0.0
                        for b in range(10):
                            m = idx == b
                            if m.sum() > 0:
                                ece += (m.sum()/len(gamma_C)) * abs(gamma_C[m].mean() - d['z'][m].mean())
                        metrics_e.append(float(ece))
                    metrics_mu.append(float(np.sqrt(np.mean((fit['mu'] - np.array([0.0, 0.4]))**2))))
                    if cohort == 'switch':
                        P_true = np.array([[0.95, 0.05], [0.20, 0.80]])
                        P_hat = np.exp(fit['log_A'])
                        metrics_P.append(float(np.linalg.norm(P_hat - P_true)))
                    ms_winners.append(diag['multistart_winners'])
                    entropies.append(np.mean(diag['entropies']))
                    hellingers.append(np.mean(diag['hellingers']))
                cohort_results[cohort] = dict(
                    hamming=float(np.mean(metrics_h)),
                    ece=float(np.mean(metrics_e)) if metrics_e else None,
                    mu_rmse=float(np.mean(metrics_mu)),
                    P_rmse=float(np.mean(metrics_P)) if metrics_P else None,
                    multistart_frac=float(np.mean(ms_winners) / 10.0),
                    entropy=float(np.mean(entropies)),
                    hellinger=float(np.mean(hellingers)),
                )
            sweeps.append(dict(beta_sell=beta_sell, a_chan=a_chan, cohorts=cohort_results))
    return sweeps

def evaluate_thresholds(sweeps):
    # Default sweep point: beta_sell=0.3, a_chan=0.6
    base = next(s for s in sweeps if s['beta_sell'] == 0.3 and s['a_chan'] == 0.6)
    sw = base['cohorts']['switch']; tr = base['cohorts']['T']; co = base['cohorts']['C']
    pf = {
        'hamming_switch': ('PASS' if sw['hamming'] <= 0.20 else 'FAIL', sw['hamming'], 0.20),
        'hamming_T': ('PASS' if tr['hamming'] <= 0.10 else 'FAIL', tr['hamming'], 0.10),
        'hamming_C': ('PASS' if co['hamming'] <= 0.10 else 'FAIL', co['hamming'], 0.10),
        'ece': ('PASS' if sw['ece'] <= 0.08 else 'FAIL', sw['ece'], 0.08),
        'mu_rmse': ('PASS' if sw['mu_rmse'] <= 0.15 else 'FAIL', sw['mu_rmse'], 0.15),
        'P_rmse': ('PASS' if sw['P_rmse'] <= 0.20 else 'FAIL', sw['P_rmse'], 0.20),
        'multistart': ('PASS' if sw['multistart_frac'] >= 0.40 else 'FAIL', sw['multistart_frac'], 0.40),
        'entropy': ('PASS' if sw['entropy'] <= 0.38 else 'FAIL', sw['entropy'], 0.38),
    }
    return pf

def main():
    p = argparse.ArgumentParser()
    p.add_argument('--seed', type=int, default=20260426)
    p.add_argument('--out', type=str,
                   default=os.path.join(os.path.dirname(os.path.abspath(__file__)), 'outputs'))
    args = p.parse_args()
    os.makedirs(args.out, exist_ok=True)
    t0 = time.time()
    sweeps = run_sweep(args.seed)
    pf = evaluate_thresholds(sweeps)
    elapsed = time.time() - t0
    out = dict(seed=args.seed, elapsed_sec=elapsed, sweeps=sweeps, pass_fail=pf)
    with open(os.path.join(args.out, 'results.json'), 'w') as f:
        json.dump(out, f, indent=2, default=str)
    # Markdown summary
    lines = ['# Layer 2 §4 validation results', f'seed={args.seed}, elapsed={elapsed:.1f}s', '',
             '## Pass/fail (default sweep: beta_sell=0.3, a_chan=0.6)', '']
    lines.append('| Metric | Value | Threshold | Verdict |')
    lines.append('|---|---|---|---|')
    for k, (verdict, val, thr) in pf.items():
        lines.append(f'| {k} | {val:.4f} | {thr} | {verdict} |')
    lines.append('')
    lines.append('## Full sweep grid (Hamming on switching cohort)')
    lines.append('')
    lines.append('| beta_sell | a_chan | Hamming(switch) | ECE | mu_rmse | P_rmse | multistart_frac | entropy |')
    lines.append('|---|---|---|---|---|---|---|---|')
    for s in sweeps:
        c = s['cohorts']['switch']
        lines.append(f"| {s['beta_sell']} | {s['a_chan']} | {c['hamming']:.3f} | "
                     f"{c['ece']:.3f} | {c['mu_rmse']:.3f} | {c['P_rmse']:.3f} | "
                     f"{c['multistart_frac']:.3f} | {c['entropy']:.3f} |")
    with open(os.path.join(args.out, 'results.md'), 'w') as f:
        f.write('\n'.join(lines))
    print('\n'.join(lines))

if __name__ == '__main__':
    main()
