# Narrative Atlas — Layer 2: Insider Divergence

**Status:** Draft v0.2 — Thread A specification integrated; v0 validation harness present and executed end-to-end with NUMBERS_DIFFER outcome (see §11.2). Specification committed but not yet empirically validated. Not yet implemented in production. To be refined as Threads B, C, D, and E (§17) complete and the v1 harness expansion root-causes the v0 threshold failures.

**Scope:** This document defines what Layer 2 *is*, what it *emits*, what it *depends on*, and what is deliberately deferred. It is the single source of truth for Layer 2 design decisions. When Layer 2 is implemented, the implementation must be traceable to commitments in this document; when those commitments are revised, the document is updated and versioned.

**Audience:** A future contributor to Narrative Atlas, a technical reviewer, or the author six months from now trying to remember why a specific design choice was made. Every non-obvious commitment carries either a citation or an explicit "this is a configurable choice, here is the reasoning."

---

## 1. Purpose

Layer 2 of the Narrative Atlas platform is the **Insider Divergence** layer. Its job is to estimate, for each (firm, executive, time) triple, the posterior probability that the executive is in a *concealing state* — a state in which the executive's external-facing narrative (what they say in earnings calls, press releases, SEC filings, IR communications) is inconsistent with their private actions (what they do via Form 4, Form 144, and related filings on the same firm's stock).

This is the layer that operationalizes the platform's foundational thesis: **say-do divergence is a higher-quality signal than either say or do alone**, because both are downstream emissions of the same underlying agent, and inconsistency between them is diagnostic of strategic information-asymmetry behavior that no single channel will reveal.

Layer 2 is *not* an insider-trading-alpha factor. The academic literature on insider-trading alpha — Lakonishok-Lee (2001), Cohen-Malloy-Pomorski (2012), Ali-Hirshleifer (2017), and the Ozlen-Batumoglu (2025) decay finding — is a thoroughly mined area, and the post-publication, post-decay, post-cost residual is small. Several public ETFs (Invesco NFO, Direxion KNOW) already trade roughly that signal at modest scale and with modest results. If Narrative Atlas's Layer 2 were a re-implementation of CMP-style opportunistic-only insider trading, it would have low capacity, low t-statistic, and no defense against the question "why does this exist."

What Layer 2 *is*, instead, is the divergence layer. The asset is not "insider buys outperform" — that's a known and arbitraged signal. The asset is "the executive is currently behaving in a way that is jointly improbable under any single belief state about the firm." That is a different and less-mined object. Whether it is also tradeable is an empirical question that this document specifies how to answer rigorously, but the layer's value to the platform is not contingent on a tradeable alpha — it is contingent on the divergence posterior being a useful conditioning variable for downstream layers and for the eventual cross-layer composition. Even at zero alpha, a clean concealment posterior is information that no other commercial product on the market produces in this form.

---

## 2. Architectural placement

The Narrative Atlas vision is a five-layer model of corporate information state. The layers are not parallel; they compose.

- **Layer 1 — Regulatory filings.** Drift in formal disclosure language (10-K/Q, 8-K, S-1) over time. Builds on Cohen-Malloy-Nguyen (2020) "Lazy Prices" and the broader textual-change literature. *Not yet implemented.*
- **Layer 2 — Insider divergence (this document).** Bayesian state estimator over a hidden concealment process per (firm, executive). Consumes narrative observation channels from Layers 1 and 4 plus action observations from Form 4 / Form 144 / Form 5.
- **Layer 3 — Aspect-level sentiment.** Refines belief estimates to the segment / geography / product-line level. *Not yet implemented.*
- **Layer 4 — Public discourse sentiment.** The proof-of-concept layer. Implemented for the CSCI 4535 final project; produces firm-day-level sentiment across three methods (VADER, LogReg, FinBERT). Currently corpus is the FinancialPhraseBank; the production version will consume earnings call transcripts and press releases.
- **Layer 5 — Cross-source divergence aggregation.** Higher-order layer combining cross-layer signals into a single firm-level state estimate. *Not yet specified.*

Layer 2 is architecturally distinguished from the other layers in one important respect: every other layer in the platform is producing *observations* or refining the *granularity* of those observations. Layer 2 is the layer that *fuses* observations into a posterior over a latent state. It is a state estimator, not a measurement.

This distinction matters because it tells you what Layer 2's contract with the rest of the platform looks like. Layer 2 consumes a typed list of observation channels (some from Layer 1, some from Layer 4, plus the action vector from EDGAR) and emits a single typed object: the per-(firm, executive, time) posterior probability of the concealing state, together with provenance and uncertainty metadata. Downstream consumers — Layer 5, future products, analytical UI — bind to that posterior. They never look inside Layer 2's machinery.

The architectural commitment in one sentence: **Layer 2 is a Bayesian state estimator over a hidden concealment process, fed by typed observation channels from other layers, emitting a posterior probability that downstream consumers depend on through a stable contract.**

---

## 3. Conceptual foundation

### 3.1 Companies as narrative producers

The deepest mistake in early thinking about this layer was framing "say" and "do" as two independent signals that could be measured and subtracted. They are not independent. They are two outputs of the same agent. A company — and the executives running it — continuously produces narrative (earnings calls, press releases, 10-K/Q language, 8-K disclosures, investor-day decks, sponsored sell-side coverage, social-media presence, IR consultation with analysts) and continuously takes action (open-market trades, exercises, gifts, stock-based compensation choices, dividend and buyback policy). Both narrative and action flow from the same underlying state — the executive's actual private information about the firm — passed through the same agent's strategic-choice filter.

A model that treats sentiment and trading as orthogonal observables, and "divergence" as their signed difference, misses the point. The right framing is: there is a hidden state (what the executive privately believes and intends), and there are multiple correlated observations (what the executive says, what the executive does, how often, through which channels, with what tone). The job of the layer is to estimate the hidden state given the joint distribution of the observations, not to compute a difference between two of them.

### 3.2 The identification problem

The strongest argument against a naive say-minus-do construction is the identification problem. Consider the canonical scenario the layer is supposed to detect: an executive who knows the firm is in trouble, talks bullishly to maintain the stock price, and sells personal holdings into that strength.

Under a naive construction, this looks like a clean (Say+, Do−) divergence event. But under any reasonable data-generating model, the bullish talk *is itself caused by the concealment intent*. The executive is not bullish-by-coincidence and selling-by-coincidence on the same day; the bullishness is *part of the concealment strategy*. So we are not observing two independent signals diverging — we are observing two correlated symptoms of the same latent state.

Mechanically:

- $P(\text{Say+}, \text{Do−} | \text{concealing}) \gg P(\text{Say+}, \text{Do−} | \text{transparent})$,
- but the bullish-talk and the bearish-trade are *dependent given the latent state*, because both are downstream of the same concealment intention.

This is a textbook latent-confounder structure and the academic literature has been here for decades:

- **Kothari, Shu, Wysocki (2009)**, "Do Managers Withhold Bad News?" — managers asymmetrically delay bad news and accelerate good news.
- **Niessner (2015)** — top managers are "more than twice as likely to strategically time disclosures if the return under-reaction benefits their insider sales."
- **Ali & Hirshleifer (2017)** — opportunism is a *firm-and-managerial trait*, not a per-trade event; the same managers who trade opportunistically are systematically more likely to be involved in misconduct, fraud, and accounting restatements.

The implication is that Layer 2's estimand cannot be a function of the marginals of say and do. It has to be a function of their joint distribution, conditioned on covariates that absorb known mechanical correlation channels (price strength, earnings surprise sign, momentum, stock-based compensation cycle).

The formal mathematical demonstration that the §4 specification encodes this dependence structure — that the hierarchical HMM's marginal over $(s, d)$ exhibits exactly the latent-confounder dependence the argument above asserts is present, and that the dependence vanishes upon conditioning on the latent state — appears at §4.7. That subsection is the proof that the §4 model does what §3.2 claims it should.

### 3.3 The estimand

Given the above, the formal Layer 2 estimand is:

$$\text{divergence}_{i,e,t} = P(z_{i,e,t} = \text{concealing} \mid \mathbf{s}_{i,t}, d_{i,e,t}, \mathbf{x}_{i,t})$$

where $z$ is a latent state for firm $i$, executive $e$, at time $t$; $\mathbf{s}$ is a multi-channel narrative observation vector (from Layers 1 and 4); $d$ is the action observation (from EDGAR); and $\mathbf{x}$ is a vector of controls absorbing known mechanical correlations.

The key point: this is a posterior over a latent state given correlated observations and controls. It is not a difference. It is not a residual from a single regression. It is a Bayesian inference object, and that has implications for how the layer is built, calibrated, and validated.

---

## 4. The model

This section commits to the v1 specification produced by Thread A. The full mathematical derivation, the comparison against alternatives (residualized regression, mutual information, conditional probability ratio, linear-Gaussian state-space), and the runnable validation harness live in `docs/layers/layer_2/research/Insider Divergence Detection as Bayesian HMM Spec with Covariate-Dependent Emission.md`. This section is the design-document commitment that the research document supports; it is the source of truth for what Layer 2 v1 *is*. When Thread A's harness expansion produces v1.x revisions, those revisions are integrated here.

### 4.1 State space and cardinality

The latent state is binary: $z_{i,e,t} \in \{T, C\}$ — Transparent and Concealing. The argument against expansion to three or four states is quantitative and substantive. Quantitatively, the post-SOX-only window for any given executive contains roughly 10–200 observations; a $K$-state HMM with $C$ continuous channels and $p$ covariates has approximately $K(K-1) + K \cdot C(p+2)$ free parameters before hierarchical pooling, which for the committed $C = 9$, $p = 8$ already exceeds typical per-executive observation counts at $K = 2$ and motivates hierarchical pooling as a hard requirement. $K = 3$ doubles the entropy of the role-level transition prior and forces three-way pairwise distance between emission distributions to be detectable, which fails at typical signal-to-noise ratios in synthetic-data validation.

Substantively, the §3.2 latent-confounder argument is fundamentally binary: the executive either is or is not in possession of material non-public information unfavorable to the asserted narrative. A three-state extension ("transparent / partially concealing / fully concealing") requires an ordering on concealment intensity, which is not directly observable and would be identified only via the magnitude of opportunistic trades — a tautological circle that collapses to label-only differentiation. A "transparent / concealing-bullish / concealing-bearish" extension is the natural three-state alternative; it duplicates the same hidden bit and is better encoded as state × narrative-direction with state remaining binary and narrative-direction observed through the sign of the narrative emission. We adopt the latter encoding implicitly.

The decision: $K = 2$, $z_t \in \{T, C\}$, with the label-fixing constraint $\mu_T^{(\text{narr})} < \mu_C^{(\text{narr})}$ on the pooled-over-channels narrative-sentiment marginal, applied post-hoc by Stephens (2000) KL alignment across multi-start runs.

### 4.2 Transition kernel — hierarchical multinomial-logit with role-level pooling

For executive $i$ with role $r(i) \in \{\text{CEO, CFO, COO, other-NEO}\}$ and industry $\iota(i)$, define the per-row transition logit

$$\eta_i = \big(\eta_i^{TC},\, \eta_i^{CT}\big) \in \mathbb{R}^2, \qquad P_i = \begin{pmatrix} \sigma(-\eta_i^{TC}) & \sigma(\eta_i^{TC}) \\ \sigma(\eta_i^{CT}) & \sigma(-\eta_i^{CT}) \end{pmatrix},$$

with $\sigma$ the logistic CDF. The hierarchy is two-level on role with industry as a fixed covariate, not a third level; industry-level pooling is rejected because the cross-product role × industry partition gives roughly 40 cells, many of which contain five or fewer executives in the realistic universe and cannot support a Level-2 normal hyperprior.

$$\eta_i \mid r(i),\, \iota(i) \;\sim\; \mathcal{N}\!\big(\mu_{r(i)} + \Gamma\, \iota(i),\; \Sigma_\eta\big),$$

$$\mu_r \;\sim\; \mathcal{N}(\mu_0,\, \Sigma_0), \qquad r \in \{\text{CEO, CFO, COO, other-NEO}\},$$

$$\mu_0 = (\,\text{logit}(0.05),\, \text{logit}(0.20)\,)' \quad \text{(stationary prior: } T \text{ persistent, } C \text{ less so)},$$

$$\Sigma_0 = 4 I_2, \qquad \Sigma_\eta = \tau^2 I_2 \text{ with } \tau \sim \text{Half-Cauchy}(0,\,1),$$

$$\Gamma \in \mathbb{R}^{2 \times d_\iota} \;\sim\; \mathcal{N}(0,\, I).$$

The prior mean $\mu_0$ encodes weak prior persistence of $T$ — transitioning out at logistic rate 0.05 per week, roughly a 14-week mean dwell — and shorter $C$ episodes — transitioning out at rate 0.20 per week, roughly a 5-week dwell — reflecting our prior that concealment episodes are bounded by the disclosure cycle. The wide $\Sigma_0$ allows the role-level posterior to swing one to two orders of magnitude in transition probability if the data demand it.

Hyperparameters $(\mu_r, \Sigma_\eta, \Gamma, \tau)$ are estimated by Type-II marginal-likelihood maximization for v1.0 — a two-step nested EM, outer loop on hyperparameters, inner loop the per-executive forward-backward EM with the current hyperparameters as fixed prior. This is the Altman (2007) MHMM Type-II ML procedure adapted to multinomial-logit transitions; full hierarchical Bayes with NUTS (Mildiner Moraga & Aarts 2024) is the v1.x upgrade path.

Hierarchical pooling is a hard requirement, not an optimization. The post-SOX universe's observation-count distribution has its 10th percentile at 14 observations and its 25th percentile at 22; the rule-of-thumb count for per-executive transition-matrix estimability is roughly $10 K(K-1) = 20$ observations conditional on having experienced at least one observed transition. Approximately 60% of executives fall below per-executive estimability and rely on the pool.

Semi-Markov durations are deferred to v2. Hadj-Amar–Jewson–Fiecas (2023) document Bayes factors of order $e^{2.9}$ favoring negative-binomial over geometric durations on telemetric data, with corresponding 10–30% bias on mean dwell times when geometric is mis-specified. Our synthetic-data validation in §11 explicitly tests whether geometric durations bias state recovery; the hypothesis is rejected for our parameter regime when state-recovery degradation is below the 0.04 threshold. Semi-Markov is reopened only if that test reveals degradation above threshold.

### 4.3 What "channels" means concretely

The HMM specification has the latent state emitting observations across $C = 9$ narrative channels and one action vector. Concrete enumeration of the narrative channels:

| Channel | Source | Description |
|---|---|---|
| $c=1$ | Layer 4 | Sentiment of CEO's prepared remarks (earnings call) |
| $c=2$ | Layer 4 | Sentiment of CEO's Q&A responses (earnings call) |
| $c=3$ | Layer 4 | Sentiment of CFO's prepared remarks |
| $c=4$ | Layer 4 | Sentiment of CFO's Q&A responses |
| $c=5$ | Layer 4 | Press release tone (firm-aggregated, periodicized) |
| $c=6$ | Layer 1 | 10-K/Q risk-factor language drift (Lazy Prices–style) |
| $c=7$ | Layer 1 | 8-K event-disclosure tone |
| $c=8$ | Layer 4 (extension) | Narrative cadence — count of press releases, 8-Ks, conference appearances per quarter, normalized by firm size |
| $c=9$ | Layer 4 (extension) | Narrative effort intensity — total external-comm word count per quarter |

Channels 1–5 require speaker-attributed Layer 4, which Layer 4 does not currently produce (the CSCI 4535 proof-of-concept is firm-day, not executive-utterance). Building speaker attribution into Layer 4 is Thread C (§17). Channels 6–7 require Layer 1, which is not yet implemented; in the absence of Layer 1, Layer 2 can run with channels 1–5 and 8–9 only, with the understanding that the formal-disclosure side is missing and the posterior is correspondingly less informative.

The $C \times $ executive design space is what makes Layer 2 a fusion layer. With six executives covered (CEO, CFO, COO, CIO, GC, board chair) and nine channels, the observation space is 54-dimensional per firm-quarter, plus the action vector. That dimensionality is *the asset* — it is what makes Layer 2 hard to replicate from a single data source and what makes the posterior informative when no individual channel would be.

### 4.4 Emission distributions

The action vector is $d_t = (\delta_t,\, \log s_t,\, \kappa_t,\, o_t,\, \pi_t)$: direction $\delta_t \in \{-1, 0, +1\}$, log size, transaction code $\kappa_t \in \{P, S, A, F, M, \text{other}\}$, opportunistic flag $o_t \in \{0, 1\}$ (Cohen–Malloy–Pomorski 2012 routine/opportunistic classifier output), and 10b5-1 flag $\pi_t \in \{0, 1, \text{NA}\}$ with NA prior to April 1, 2023. The covariate vector $x_t \in \mathbb{R}^p$ has $p = 8$ entries: rolling firm return at three horizons (1w, 4w, 26w), market and industry-momentum factor returns, vesting-event indicator, ownership-stake percentile, log-firm-size, and the post-2023-regime dummy.

Channels factorize given $(z_t, x_t)$:

$$p(s_t^{(1)}, \dots, s_t^{(9)},\, d_t \mid z_t,\, x_t;\, \theta) \;=\; \Big(\prod_{c=1}^{9} f_c(s_t^{(c)} \mid z_t,\, x_t;\, \theta_c)\Big) \cdot g(d_t \mid z_t,\, x_t;\, \phi).$$

This is the single-chain product-emission specification (Cappé–Moulines–Rydén 2005 §1.3). The factorization is over channels, *not* over channels and the action; the §3.2 latent-confounder structure operates by channel-action dependence routed through $z_t$, which the factorization preserves and §4.7 demonstrates. Cross-channel residual covariance — for example, CEO-prepared and CEO-Q&A from the same call — is acknowledged and handled by including a call-fixed-effect in the covariate $x_t$.

Narrative-channel emissions are skew-normal with state-dependent location and scale, common shape, and covariate-driven location:

$$s_t^{(c)} \mid z_t = k,\, x_t \;\sim\; \mathrm{SN}\!\big(\mu_k^{(c)} + \beta_c' x_t,\; \omega_k^{(c)},\; \alpha^{(c)}\big), \qquad k \in \{T, C\}.$$

Skew-normal is preferred over Gaussian because narrative-sentiment scores in the Loughran–McDonald and Larcker–Zakolyukina literatures show systematic right-skew in prepared remarks and left-skew in Q&A under stress. The slope $\beta_c$ is **state-invariant** — this is the binding identification choice, addressed in §4.8. The variance is **state-dependent** ($\omega_k^{(c)}$): the concealment regime exhibits compressed sentiment dispersion (Hoberg–Lewis 2017 "grandstanding").

The action emission factorizes into five components:

$$g(d_t \mid z_t = k,\, x_t;\, \phi) \;=\; g_\delta(\delta_t \mid z_t=k, x_t)\; \cdot\; g_s(\log s_t \mid \delta_t, z_t=k, x_t)\; \cdot\; g_\kappa(\kappa_t \mid z_t=k, x_t)\; \cdot\; g_o(o_t \mid z_t=k, x_t)\; \cdot\; g_\pi(\pi_t \mid z_t=k, x_t, t).$$

Conditioning $\log s_t$ on $\delta_t$ is necessary because $\log s_t = -\infty$ when $\delta_t = 0$ — no trade. The size factor $g_s$ is a degenerate point-mass at $-\infty$ when $\delta_t = 0$ and a Gaussian on the log-shares-traded support when $\delta_t \ne 0$.

Direction is categorical: $\delta_t \mid z = k, x_t \sim \text{Categorical}(\text{softmax}(\nu_k + \Theta_k x_t))$, with reference category $\delta = 0$ fixed. Size given non-zero direction is Gaussian: $\log s_t \mid \delta_t = \pm 1, z = k, x_t \sim \mathcal{N}(a_{k,\delta_t} + b_{\delta_t}' x_t, \rho_{k,\delta_t}^2)$, with the slope $b_{\delta_t}$ state-invariant so that mechanical price-volume coupling — the "sell into strength" effect of Lakonishok–Lee 2001 and Jeng–Metrick–Zeckhauser 2003 — is absorbed into $b' x_t$, leaving the state intercept $a_{k,\delta_t}$ to capture the residual concealment signal. Transaction code is categorical: $\kappa_t \mid z = k, x_t \sim \text{Categorical}(\text{softmax}(\gamma_k + \Lambda_k x_t))$ with reference category P; the discriminative weight sits on the P/S contrast, since F (tax withholding) and M (option exercise) are mechanical. Opportunistic flag is Bernoulli: $o_t \mid z = k, x_t \sim \text{Bernoulli}(\sigma(\xi_k + \zeta' x_t))$. The Cohen–Malloy–Pomorski 3-year same-month classifier produces this label upstream as a feature, which the model treats as an emission rather than a covariate.

The 10b5-1 flag is regime-conditional. For $t < t^*$ where $t^* = $ April 1, 2023, the factor $g_\pi$ is *missing* — dropped from the likelihood — because the field did not exist. For $t \ge t^*$:

$$\pi_t \mid z = k, x_t, t \ge t^* \sim \text{Bernoulli}\big(\sigma(\psi_k + \chi' x_t)\big).$$

Treatment as a regime-conditional emission with state-dependent intercept $\psi_k$, separate from the pre-$t^*$ era, is preferred to a covariate $I(t \ge t^*)$ interaction inside a single Bernoulli emission because the pre-$t^*$ data carry no information about $\psi_k$ and pooling them with a missing-indicator covariate would push the pre-$t^*$ Bernoulli mean toward zero spuriously. The Lenkey (2014) and post-2023 amendments — SEC Release 33-11138 effective February 27, 2023; Form 4 checkbox effective April 1, 2023; mandatory 90/120-day cooling-off; single-plan-per-12-months — collectively imply that $\psi_C - \psi_T$ should be smaller post-$t^*$ than the structural-break-implied counterfactual would predict, because concealment via 10b5-1 plans becomes more procedurally costly. We model $\psi_k$ as constant post-$t^*$ and report sensitivity to a further pre-/post-August-2023 split.

All state-conditional emission intercepts $\{\mu_k^{(c)}, a_{k,\delta}, \gamma_k, \nu_k, \xi_k, \psi_k\}$ for executive $i$ are drawn from role-level normal distributions with hyperparameters estimated by Type-II ML, mirroring the transition-kernel hierarchy. Slopes $\{\beta_c, b_\delta, \zeta, \chi, \Theta_k, \Lambda_k\}$ are pooled to the global level — no role-level random effects on slopes — based on the principle that mechanical price-volume coupling is a market-wide phenomenon and role-level slope variation would over-fit.

### 4.5 Time discretization and asynchronous observations

The grid is discrete weekly: $t \in \{1, 2, \dots, T\}$ with $\Delta t = 7$ days. Continuous-time HMM is rejected for v1.0; Liu et al. (2015) NeurIPS efficient-EM CT-HMM is feasible single-executive but does not have mature tooling for three-level hierarchical priors over rate matrices, and the sampling cadence is dominated by quarterly earnings calls (regular) and weekly returns (regular), with only Form 4 and 8-K being event-driven. Sanchez et al. (2024) show CT-HMM and discretized HMM yield equivalent MLEs under regular sampling, so the discretization sacrifices nothing on the regularly-sampled channels.

Channel availability follows a missing-at-random factorization on the narrative side and an informative-absence emission on the action side. For each executive-week $(i, t)$ and each channel $c$, define availability $A_{i,t}^{(c)} \in \{0, 1\}$. The likelihood contribution at time $t$ is

$$\eta_{i,t}(k) \;=\; \prod_{c : A_{i,t}^{(c)} = 1} f_c(s_{i,t}^{(c)} \mid z = k, x_{i,t}) \cdot \prod_{c : A_{i,t}^{(c)} = 0} 1.$$

This is the Rabiner (1989) §VI.D.4 / Yu–Kobayashi (2003) MAR-marginalization. Forward-backward is unchanged in form.

Action-channel absence is *not* MAR. Gao–Ma–Ng–Wu (2022) document that insider silence — the absence of Form 4 trades over a window — is a stronger negative signal than observed selling, especially in high-litigation-risk firms. We model action absence as an additional binary emission:

$$A_{i,t}^{(\text{Form4})} \mid z = k, x_{i,t} \;\sim\; \text{Bernoulli}\big(\sigma(\lambda_k + \theta' x_{i,t})\big),$$

with $\lambda_C > \lambda_T$ a priori — the concealment regime is more silent — and $x_{i,t}$ including litigation-risk proxies (firm sector, recent restatement indicator, analyst coverage). Narrative-channel availability remains MAR, since earnings calls happen on a regulatory schedule independent of the latent state, and is dropped from the likelihood when absent.

The likelihood contribution from a partially-observed time slice $t$ for executive $i$ is then

$$\eta_{i,t}(k) \;=\; \Big(\prod_{c=1}^{9} f_c(s_{i,t}^{(c)} \mid z = k, x_{i,t})^{A_{i,t}^{(c)}}\Big) \cdot \Big(g(d_{i,t} \mid z = k, x_{i,t})^{A_{i,t}^{(\text{Form4})}} \cdot \big[1 - \sigma(\lambda_k + \theta' x_{i,t})\big]^{1 - A_{i,t}^{(\text{Form4})}}\Big).$$

The action-availability factor enters every time slice; the action-content factor enters only when Form 4 is present.

### 4.6 Likelihood, EM, and computational cost

Given hyperparameters $\Phi = (\mu_r, \Sigma_\eta, \Gamma, \tau, \text{global slopes})$, the per-executive full-data likelihood is

$$\mathcal{L}_i(\theta_i \mid y_i, x_i; \Phi) \;=\; p(\theta_i \mid \Phi) \cdot \sum_{z_{1:T_i}} \pi_{i,1}(z_1) \prod_{t=2}^{T_i} P_i(z_t \mid z_{t-1}) \cdot \prod_{t=1}^{T_i} \eta_{i,t}(z_t),$$

where $\theta_i$ collects per-executive state-conditional intercepts and the transition logits $\eta_i$. The full panel likelihood is $\prod_{i=1}^{N} \mathcal{L}_i$; the marginal Type-II likelihood after integrating $\theta_i$ against $p(\theta_i \mid \Phi)$ is what is maximized over $\Phi$ in the outer EB loop.

The Layer 2 commitment is to the *smoothed* posterior — forward-backward over the entire executive history, not real-time filtering — because the use case is retrospective divergence assessment, not live alpha generation. Filtered posteriors $\Pr(z_t \mid y_{1:t})$ are also computed and logged for online-update use cases; see §15.

EM operates in log-space throughout via `scipy.special.logsumexp`. The E-step computes the log-emission matrix $\log \eta_{i,t}(k)$ for $k \in \{T, C\}$ from current $\theta_i^{(j)}$ and runs log-space forward and backward to produce $\log \alpha$, $\log \beta$, $\log \gamma$, $\log \xi$. The M-step is prior-augmented: a one-step Newton update on the multinomial-logit transition rows; a closed-form Gaussian-prior shrinkage update on the skew-normal narrative intercepts; analogous IRLS updates on the multinomial-logit and Bernoulli emissions. After all $N$ executives have completed their inner-loop EM (parallelized across executives, embarrassingly), the hyperparameters $\Phi$ are re-estimated by closed-form Gaussian moment-matching on the posterior modes $\hat\theta_i$ with the Morris (1983) debiasing correction. The outer loop terminates when $\|\Phi^{(j+1)} - \Phi^{(j)}\| / \|\Phi^{(j)}\|$ falls below $10^{-3}$.

K = 10 multi-start is mandatory. Per-executive EM is run from 10 initializations: 4× k-means-seeded, 4× random-posterior, 2× random-parameter-from-data-moment-box (Biernacki–Celeux–Govaert 2003). Stephens (2000) KL-relabeling aligns the 10 solutions; the converged log-likelihood distribution is logged. The mode with the highest aligned log-likelihood is selected. If the top-2 modes' log-likelihoods differ by less than $10^{-3} \cdot |\ell^*|$ but their state-conditional emission means $\hat\mu_T, \hat\mu_C$ disagree by more than 2 pooled SDs, the executive is flagged "weakly identified" and its posterior is replaced by the role-level prior — the cold-start fallback documented in §15.

Computational cost is tractable. Per-executive forward-backward is $O(K^2 T_i) = O(4 T_i)$ time and $O(K T_i) = O(2 T_i)$ memory. Per-executive EM inner loop is roughly 50 iterations × $K = 10$ starts × $O(T_i)$, which is $\sim 500 T_i$ FB-equivalent ops. For a 1000-executive population at a mean $T_i = 50$, this is $\sim 2.5 \times 10^7$ FB ops per outer iteration, dominated by emission-likelihood arithmetic over $p \approx 8$ covariates plus 9 narrative + 5 action components. On a single CPU core at $\sim 10^7$ flops/sec for vectorized numpy, the inner sweep is roughly 10 minutes; 10 outer iterations is roughly 2 hours; embarrassingly parallel across executives reduces to minutes on a 32-core node. A 20-year backtest with quarterly point-in-time fits — 80 fits at 2 hours single-core — is roughly 160 core-hours, roughly 5 wall-clock hours on a 32-core node.

### 4.7 Latent confounder structure

The specification encodes the §3.2 dependence structure. Define $s^+ = \{s_t^{(c)} > \mu_T^{(c)} + \omega_T^{(c)}\}$ as "bullish narrative" and $d^- = \{\delta_t = -1\} \cap \{o_t = 1\}$ as "opportunistic selling." Under the conditional-independence-given-state factorization,

$$\Pr(s^+, d^- \mid z = C, x) = \Pr(s^+ \mid z = C, x) \cdot \Pr(d^- \mid z = C, x).$$

Marginally, integrating out $z$ at the population stationary distribution $\pi^* = (\pi_T^*, \pi_C^*)$,

$$\Pr(s^+, d^- \mid x) = \pi_T^* \Pr(s^+ \mid T, x)\Pr(d^- \mid T, x) + \pi_C^* \Pr(s^+ \mid C, x)\Pr(d^- \mid C, x),$$

$$\Pr(s^+ \mid x)\Pr(d^- \mid x) = \big[\pi_T^* p_T^s + \pi_C^* p_C^s\big]\big[\pi_T^* p_T^d + \pi_C^* p_C^d\big]$$

with shorthand $p_k^s = \Pr(s^+ \mid k, x)$, $p_k^d = \Pr(d^- \mid k, x)$. The marginal joint exceeds the marginal product if and only if

$$\pi_T^* \pi_C^* (p_T^s - p_C^s)(p_T^d - p_C^d) < 0,$$

which holds exactly when $\Pr(s^+ \mid C) > \Pr(s^+ \mid T)$ — concealment is bullish-talkative — and $\Pr(d^- \mid C) > \Pr(d^- \mid T)$ — concealment is bearish-trading. Both conditions are the substantive content of §3.2. The HMM thus implies positive marginal dependence between $s^+$ and $d^-$ even though the conditional dependence given $z$ is zero. This is the latent-confounder representation: the hidden $z$ induces marginal dependence between observable $s$ and $d$ that disappears upon conditioning on $z$.

A naive specification that posits conditional independence of $s$ and $d$ given $x$ but no latent state collapses to $\Pr(s, d \mid x) = \Pr(s \mid x)\Pr(d \mid x)$, which equals the HMM's marginal only when $p_T^s = p_C^s$ or $p_T^d = p_C^d$ — the very degeneracy that violates Conditions I2 / I7 below. The naive model is the boundary case where the hidden state has no discriminative content. The HMM strictly nests the naive specification and adds one bit of latent information that the §3.2 argument insists is present.

### 4.8 Identifiability conditions

Generic identifiability up to label permutation holds under the following conditions, applying Allman–Matias–Rhodes (2009) Theorem 6 and Gassiat–Cleynen–Robin (2016) Theorem 1, with the covariate-dependent extension of David–Bellot–Le Corff–Lehéricy (2024) and the coverage condition of Hennig (2000) and Kasahara–Shimotsu (2009).

**Condition I1 (Markov-chain primitivity).** $P_i$ is irreducible and aperiodic with $\det P_i \ne 0$. Hierarchical-prior support on logit-space rules out absorbing states with prior probability one and posterior probability one.

**Condition I2 (Linear independence of state-conditional emissions).** For at least one channel $c$ on a positive-measure subset of the covariate support $\mathcal{X}$, the measures $f_c(\cdot \mid z = T, x)$ and $f_c(\cdot \mid z = C, x)$ are not equal as elements of the space of finite signed measures. Equivalently, $\mu_T^{(c)} \ne \mu_C^{(c)}$ or $\omega_T^{(c)} \ne \omega_C^{(c)}$ for some $c$.

**Condition I3 (Three-observation rule under GCR).** For each executive $i$, $T_i \ge 3$. Trivially satisfied.

**Condition I4 (Coverage condition, Hennig 2000).** The covariate support $\mathcal{X}$ is not contained in any single hyperplane on which $\beta_c' x = a_{k,\delta} - a_{k',\delta}$ for all $k \ne k'$. Equivalently, $x_t$ varies on a strictly two-dimensional subspace, satisfied by the inclusion of two independent rolling-return horizons.

**Condition I5 (Rank condition, Kasahara–Shimotsu 2009 Prop. 6).** The matrix $[g_k(d \mid x^{(\ell)})]_{k,\ell}$ over distinct covariate values has rank 2. Under our Bernoulli/Categorical action emissions with state-dependent intercepts and at least one continuous covariate, this is generic.

**Condition I6 (Non-absorption / projection condition — the binding constraint).** For at least one channel $c$ or action-emission component,

$$\mathbb{E}\!\left[\big(s_t^{(c)} - \mathbb{E}[s_t^{(c)} \mid x_t]\big) \cdot \mathbb{1}\{z_t = C\}\right] \ne 0.$$

Equivalently, the residual after partialling out $x_t$ retains a state-dependent component. **This is the dominant identification risk in the committed specification.** It fails when the covariate vector $x_t$ contains a near-perfect proxy for $z_t$ — for instance, when post-2023 the 10b5-1 flag itself is included in $x_t$ rather than as an emission, which would absorb the state. Our specification places the 10b5-1 flag *as an emission*, not a covariate, precisely to avoid this. The opportunistic flag from Cohen–Malloy–Pomorski is similarly placed as an emission. Mechanical price-volume controls (rolling returns) enter $x_t$ because they are pre-state mechanical drivers; the litmus test for whether a variable belongs in $x_t$ or as an emission is whether the variable is causally upstream of the state (covariate) or downstream / co-determined (emission).

**Condition I7 (Distinct emission parameters).** $(\mu_T^{(c)}, \omega_T^{(c)}) \ne (\mu_C^{(c)}, \omega_C^{(c)})$ for at least one $c$, and analogously for at least one action-component intercept.

**Condition I8 (Label normalization).** Stephens (2000) KL-aligned $\hat\mu_T^{(c^*)} < \hat\mu_C^{(c^*)}$ on the pooled narrative-sentiment marginal $c^* = $ mean of CEO-prepared and CFO-prepared sentiment. This breaks the 2!-fold permutation symmetry.

The practical pitfalls — covariate absorption, mode collapse, emission-distribution near-collapse, multi-start inconsistency, spurious post-2023 break — and the automated diagnostic checks that flag them are documented in the research document at §4.1.6 and exercised by the validation harness at `experiments/layer_2/hmm_validation_v0/run.py`. The harness's per-executive identifiability flag (well/weakly/unidentified) propagates into the Layer 2 output schema documented in §4.9.

### 4.9 What gets emitted

Layer 2 emits, per (firm, executive, time):

```
{
  cik:                    int,           # SEC CIK of the firm
  ticker_at_time:         str,           # ticker as of time t
  executive_cik:          int,           # SEC reporting-person CIK
  household_id:           str,           # family-rollup identifier
  role:                   enum,          # CEO, CFO, COO, GC, Director, 10pct_owner, Other
  role_weight:            float,         # learned (Thread B), not hand-set
  time:                   timestamp,     # observation time
  P_concealing:           float in [0,1],# the layer's headline output
  P_concealing_smoothed:  float in [0,1],# forward-backward smoothed
  P_concealing_filtered:  float in [0,1],# filtered (online) posterior
  posterior_uncertainty:  float,         # std dev of posterior
  identifiability_flag:   enum,          # "well" | "weak" | "unidentified" | "cold_start"
  cold_start:             bool,          # True if T_i < 18 and role-pooled prior used
  regime_post_2023:       bool,          # True if observation is at t >= April 1, 2023
  channels_observed:      list[str],     # which channels were available
  channels_missing:       list[str],     # which were imputed
  controls_used:          list[str],     # which x covariates entered
  model_version:          str,           # Layer 2 model version
  upstream_layer4_ver:    str,           # Layer 4 sentiment model version
  upstream_layer1_ver:    str | null,    # Layer 1 version, if available
  source_filing_acc_nums: list[str],     # SEC accession numbers of source filings
  computed_at:            timestamp,     # for auditability
}
```

Every Layer 2 record carries enough provenance to reconstruct the inference. This is non-negotiable for reproducibility and for technical-interview defensibility.

The design commitment: **downstream consumers of Layer 2 see a posterior probability and its uncertainty. They do not see, and should not be coupled to, the internals of the HMM, the channel weights, or the role-weight calibration.**

---

## 5. The action side

### 5.1 What goes into the $d$ vector

The action vector consumes filings from three sources:

- **Form 4** — the canonical Section 16 reporting form. Filed by officers, directors, and >10% beneficial owners within 2 business days of a reportable transaction. This is the primary action-data source.
- **Form 144** — affiliate-sale notification under Rule 144. Filed by affiliates for sales >5,000 shares or >$50,000 in any 3-month period. Form 144 is *separate* from Form 4 and captures large affiliate sales that Form 4 does not always cover cleanly. Since April 2023, Form 144 must be filed via EDGAR (not paper), so it is now machine-readable.
- **Form 5** — annual catch-up form for transactions exempt from Form 4 reporting. Lower priority than Form 4 / Form 144 but completes the coverage of executive activity that does not appear elsewhere.

The action vector is constructed from these three sources, joined to firm and executive identifiers via SEC CIK linkage. Tippee trades, family-trust trades that fall below indirect-ownership disclosure thresholds, and Rule 10b5-1 plan trades by non-officer / non-director affiliates may evade this triple. Layer 2 is *structurally blind* to that fraction of insider activity. This is acknowledged as a foundational caveat (§9.2), not a fixable bug.

### 5.2 Transaction-code disambiguation

Form 4 transactions carry codes that distinguish economically different activities. The codes Layer 2 must handle correctly:

| Code | Meaning | Layer 2 treatment |
|---|---|---|
| P | Open-market purchase | Highest informativeness for buys |
| S | Open-market sale | Highest informativeness for sells |
| A | Grant, award, or other acquisition | Mostly mechanical; suppress |
| F | Payment of exercise price or tax via stock | Mechanical; suppress |
| M | Exercise/conversion of derivative | Often paired with S; treat the S leg only |
| G | Gift | Track separately; gifts can be informative (Cline-Williamson 2017) |
| I | Discretionary transactions | Treat as S/P based on direction |
| J | Other (catch-all) | Manual review during cleaning |

The "opportunistic vs. routine" classification (Cohen-Malloy-Pomorski 2012) is a *separate* dimension applied on top of code-level filtering. CMP defines a trade as routine if the executive trades in the same calendar month for at least three of the prior five years; opportunistic otherwise. This must be computed per-executive over their full trading history, which requires backfilled Form 4 data going back several years before any analysis window.

The CMP definition is the v1 default. Ali & Hirshleifer (2017) propose an alternative — classifying executives as opportunistic based on *profitability of pre-quarterly-earnings-announcement* trades — that has stronger empirical support post-2010 and that should be added as a robustness measure in v2.

### 5.3 The April 2023 Form 4 schema change

Effective April 1, 2023, Form 4 has a **new checkbox field**: whether the reported transaction was made pursuant to a Rule 10b5-1(c) trading plan, and if so, the date of plan adoption. This was added by the SEC's December 2022 amendments to Rule 10b5-1.

Layer 2 must parse this field. Trades flagged as 10b5-1 are mechanically pre-committed and, under most interpretations, are *less* informative than non-plan trades — though the post-2023 empirical evidence is mixed (Divakaruni-Hvide-Tveiten 2026 find that abnormal returns did not decline after the reform; insiders adapted around the rule's margin). The v1 Layer 2 design treats 10b5-1 trades as a separate emission state with reduced weight; the magnitude of the reduction is a calibration parameter that Thread B (supervised role-weight learning) will fit.

This is a parser-level requirement, not a regime-recalibration question. Implementations must verify that `edgartools` (or the alternative parser in use) handles the post-April-2023 schema correctly. As of edgartools 5.x this is supported; it must be verified at build time as a test gate.

---

## 6. Role weights

### 6.1 The empirical finding

The single most-cited literature finding on insider-role informativeness is **Wang, Shin, and Francis (2012)**, who show that **CFO purchases earn approximately 5 percentage points higher 12-month abnormal returns than CEO purchases** over 1992–2002. Knewtson and Nofsinger (2014) extend this and find the gap **shrinks but persists post-SOX**, attributing the asymmetry to the "scrutiny hypothesis": CEOs trade less aggressively because they are watched more closely.

This is an empirical fact, not a stylistic preference. Any role-weighting scheme that treats CEO and CFO as equivalent (both = 1.0) is *wrong*. The defensible v1 default is **CFO > CEO**, with the magnitude of the gap to be calibrated.

A second, equally important finding from Cohen-Malloy-Pomorski (2012) themselves: the most informed opportunistic traders are **local, non-executive insiders from geographically concentrated, poorly governed firms**. This contradicts a simple "C-suite top, board lower, founder lowest" hierarchy. Specifically, mid-rank Section 16 officers and certain directors who are local to the firm's geographic concentration may carry *higher* informativeness than the conventional ranking suggests.

### 6.2 The commitment

Role weights are **learned**, not hand-set. The supervised target is misconduct / restatement / enforcement labels (SEC AAERs, litigation releases, accounting restatements) following the Ali-Hirshleifer (2017) labeling protocol. Trades by executives in firms that subsequently suffer enforcement actions provide positive labels; trades by executives in firms that do not, but with similar firm characteristics, provide negative labels. The construction of this labeled dataset is Thread B (§17).

For v0 — before Thread B completes — the document commits to the following hand-set defaults *for prototyping only*, with an explicit citation per row and the constraint that these will be replaced:

| Role | v0 weight | Justification |
|---|---|---|
| CFO | 1.0 | Wang-Shin-Francis (2012) baseline |
| CEO | 0.85 | Wang-Shin-Francis (2012) gap; Knewtson-Nofsinger (2014) |
| COO / President | 0.7 | No direct citation; interpolated |
| General Counsel | 0.6 | Information-access argument; no direct citation |
| Other Section 16 Officer | 0.55 | CMP (2012) "non-executive insider" evidence |
| Director (non-executive) | 0.4 | Lakonishok-Lee (2001) lower informativeness |
| Founder / >10% blockholder | 0.15 | Diversification motive dominates; Bezos-style negative-control evidence |

These v0 weights must be marked clearly in code as `ROLE_WEIGHTS_V0_PROTOTYPING_ONLY` and replaced by the learned values from Thread B before any quantitative claim is published.

### 6.3 What "learned" means

Thread B will produce role weights via a supervised classifier (logistic regression or gradient-boosted tree, depending on label volume) trained to predict the binary label "trade was followed by a misconduct event within 24 months." Features include role, firm size, opportunistic-vs-routine classification, transaction code, prior insider-trading history. The role coefficients (or feature importances) provide the role weights, normalized so that the maximum weight equals 1.0.

This approach has the property that the role weights are economically interpretable (they reflect predictive power against misconduct), defensible against the question "why these numbers" (because they were fit), and updatable as new enforcement data arrives.

---

## 7. Regime handling

### 7.1 The four canonical regime breaks

The literature identifies four discrete regulatory breaks affecting insider trading data:

- **Reg-FD (October 2000)** — banned selective disclosure of material information to analysts, changing the content distribution of corporate communications.
- **Sarbanes-Oxley §403 (2002)** — reduced the Form 4 filing window from "10th day of the following month" to **2 business days**. This is the largest single discontinuity in Form 4 data quality.
- **EDGAR same-day filing (2003)** — Form 4 filings became electronically searchable on filing day, eliminating the prior delay between filing and public availability.
- **Rule 10b5-1 amendments (effective February 27, 2023; Form 4 checkbox effective April 1, 2023)** — added 90-day cooling-off periods, single-trade-plan limits, certification requirements, and the new Form 4 disclosure flag.

Layer 2 v1 operates on post-SOX data only. The pre-2002 regime is structurally different (longer filing lags, lower data quality, different selection on which trades get reported when) and should not be pooled with post-SOX data without explicit regime-specific calibration.

### 7.2 EDGAR Next (September 2025)

A fifth regulatory event with operational rather than econometric implications: **EDGAR Next**, the SEC's identity-and-access modernization, became fully effective on September 15, 2025. Every Section 16 reporting person now has individual Login.gov credentials and identity-based access controls. This does not change *what* is filed but may change filing-latency distributions and possibly the population of who files. Layer 2 should monitor for distributional shifts in filing latency post-September-2025 and treat any detected break as a recalibration trigger.

### 7.3 The 2023 reform is of contested direction

The reform's *intended* effect was to reduce 10b5-1 abuse and tighten the connection between insider information and insider trading. The empirical evidence on whether it achieved this is mixed:

- **Chung & Chuwonganant (March 2026)** — post-amendment, insider trading volume falls, spreads narrow, price efficiency improves (consistent with intended effect).
- **Divakaruni-Hvide-Tveiten (CEPR DP21199, 2026)** — post-amendment, executives' abnormal returns *did not decline*; insiders shifted opportunistic behavior toward the rule's margin (consistent with adaptation, not reduction).
- **Columbia CLS Blue Sky working paper (July 2025)** — 10b5-1 trades that previously preceded negative returns now produce flat or slightly positive abnormal returns (consistent with the reform working).

For Layer 2 v1, the 2023 reform is treated as a regime break of *unknown sign*. The 10b5-1 checkbox flag enters the model as a feature; whether plan-flagged trades become a *suppression* signal or a separate-state signal is a fitted parameter. The design must not assume the direction of the reform's effect.

### 7.4 Change-point detection

Beyond the four named regulatory breaks, Layer 2 should run change-point detection (Bai-Perron 1998 or CUSUM-based) on emission-distribution parameters per channel, per quarter. Detected breaks that align with no known regulatory event are flagged for review and may indicate undocumented regime shifts — for example, the COVID Q1 2020 break, the post-pandemic rate-cycle break in 2022–2023, or industry-specific breaks (the 2023 banking stress event, for instance). This is mostly diagnostic infrastructure, but it is the kind of thing whose absence becomes embarrassing when a referee asks "did you check for regime stability."

---

## 8. Data sources

### 8.1 Decision summary

| Source | Role in Layer 2 | Verified status |
|---|---|---|
| **EDGAR (direct)** | Authoritative source for Form 4 / 144 / 5 | SEC.gov, public domain, 10 req/s rate limit, requires User-Agent header |
| **edgartools (Python)** | Primary parser for v1 | Single-maintainer (D. Gunning), MIT-licensed, current as of v5.x, handles April-2023 Form 4 schema |
| **Layline Insider Trading Dataset** | Backup / academic-grade replication source | Balogh (2023, *Scientific Data*); Harvard Dataverse; CC-BY-equivalent |
| **WRDS (via Cornell)** | Preferred source for cleansed academic dataset, *if accessible* | LSEG/Thomson Reuters Insider Filing data with cleansing codes; verify Cornell access before committing |
| **OpenInsider** | Sanity-check / screener only | No documented cleansing pipeline; not for backtests |
| **Washington Service** | Not recommended | Six-figure institutional pricing; replaceable by WRDS at zero cost if Cornell access verified |

### 8.2 Operational constraints

- **EDGAR rate limit:** 10 requests/second, with mandatory User-Agent header declaring contact information. Confirmed current as of April 2026; not changed in 2024 or 2025. Layer 2 must respect this; bulk historical pulls require throttling and overnight scheduling.
- **edgartools maintainer risk:** edgartools is a single-maintainer project (Dwight Gunning). For a project intended to be the foundation of a future quantitative platform, this is a real risk. Mitigation: keep a thin abstraction layer (`Layer2DataAccess` interface) so the parser can be swapped to the Layline dataset or to a custom EDGAR XML parser within one engineering day.
- **WRDS undergraduate access:** if the Cornell user can register an undergraduate WRDS account, the LSEG/Thomson Reuters cleansed insider-filing dataset is available at zero cost. This is the highest-quality option for academic backtests. Constraint: WRDS undergraduate accounts cannot be used during extended semester breaks; Layer 2 development must plan around that.
- **In-house cleaning effort:** building a Washington-Service-equivalent cleaning layer from raw EDGAR — handling amendments (Form 4/A), footnote parsing, transaction-code disambiguation, post-transaction holding derivation, CIK-to-ticker reconciliation, and joint-filer rollup — is realistically 80–150 hours of senior-engineer work. The estimate matters because it sets the bar for "buy versus build."

### 8.3 Rejected sources

- **XBRL-tagged Form 4** — does not exist. Form 4 has been filed as XML, not XBRL, since June 2003. References to "post-2024 SEC XBRL Form 4 initiatives" are erroneous; do not promise this in design.
- **Free aggregator APIs (e.g., uncited services)** — these typically scrape EDGAR with no quality controls and resell. Not auditable, not citable, not to be used.
- **Paid commercial Form 4 feeds (Bloomberg, FactSet)** — high quality but licensing-restricted in ways that prevent open publication and prevent commercial repurposing without licensing fees in the tens of thousands per year. Reserved for a future commercial tier of Narrative Atlas, not for v1.

---

## 9. Identification, controls, and what the layer is structurally blind to

### 9.1 Controls

The $\mathbf{x}_{i,t}$ vector entering both the narrative and action emission distributions includes, at minimum:

- Trailing-12-week stock return (controls for "insiders sell into strength")
- Sign and magnitude of most recent earnings surprise
- Fama-French 3-factor + UMD exposures, rolling 36-month
- Industry (GICS 6-digit) at time $t$
- Stock-based-compensation vesting indicator (binary, derived from RSU/PSU grant schedules where observable)
- 10b5-1 plan flag (post–April 2023, from Form 4 checkbox)
- Time-since-last-major-disclosure (8-K or earnings call), in business days
- Firm size (log market cap)
- Analyst coverage breadth (count of forecasting analysts)

The role of these controls is to absorb the *mechanical* component of the say–do correlation, leaving only the *strategic* component for the latent state to explain. Without controls, the HMM will over-attribute the mechanical correlation to the latent state, producing a posterior that is biased upward whenever the firm has had recent price strength — exactly the regime where executives sell mechanically without any concealment intent.

This is the most important specification choice in the document and the one where Thread A (mathematical formalization) will spend most of its time. The controls listed above are a v0 default; Thread A may add or substitute based on the formalization.

### 9.2 Foundational coverage caveats

Layer 2 is structurally blind to several categories of insider activity that a referee will, correctly, ask about:

- **Tippee trading.** Friends, golfing partners, sell-side analysts, and journalists who receive material non-public information do not file Form 4. Ahern (2017) documents $928M aggregate tipped-trade profits in 2009–2013. None of this appears in the action vector.
- **Family / trust / foundation trading below indirect-ownership thresholds.** Goldie-Jiang-Koch-Wintoki documented that insiders trade through family members, trusts, and foundations to camouflage opportunistic trades. Layer 2 captures the disclosed indirect ownership but not the undisclosed.
- **Structured-product economic sales.** Collars, prepaid variable forwards, and equity swaps achieve economic sale without a Form-4-classified S transaction. Some appear under code F or K and may be misclassified by the opportunistic-routine filter.
- **Non-equity wealth diversification.** An executive who diversifies private wealth into private equity, real estate, or a family office can act on private information without ever trading the firm's equity.
- **Foreign Private Issuer exemption.** Toyota, ASML, Alibaba, and similar non-US-domestic firms are exempt from Section 16; their executives do not file Form 4. Layer 2 universe is restricted to US-domestic SEC registrants.

These are not "failure modes" in the sense of bugs to be fixed. They are foundational limits on what Layer 2 can observe. The honest framing — and the one the design doc commits to — is: **Layer 2 estimates a concealment posterior conditional on the slice of executive activity that is observable through Section 16 reporting. Activity that bypasses Section 16 is invisible to the estimator, and the posterior should not be interpreted as covering it.**

### 9.3 Survivorship and selection issues in the say corpus

A subtle but severe issue: failed firms stop having earnings calls. The Layer 4 input to Layer 2 is structurally absent precisely when divergence would be most informative — pre-bankruptcy quarters, periods of acute financial distress, and the run-up to delistings. Backtests of Layer 2 must use a survivorship-bias-free firm panel (CRSP-style, with delisting returns including the −30% delisting-return convention for performance-related delistings) or the headline alpha will be overstated by 30–100 bps annualized.

The Hill-Korczak-Wang (2019) literature on insider trading in financially distressed firms is the right anchor: distressed-firm insider buying carries signal, but their sample by definition still filed. Layer 2 must explicitly handle the "missing because of failure" case in its backtest construction.

---

## 10. Failure modes

The following enumerated failure modes extend the original twelve from the research document and integrate the additions identified in the senior-reviewer pass. Each is tagged with its severity (BLOCKER must be addressed before v1; CAVEAT must be documented; FUTURE captures known limitations to be revisited).

**FM-01 (CAVEAT): 10b5-1 plan adoption obscures opportunistic intent.** Pre-2023 a major signal-eraser; post-2023 partially mitigated by the Form 4 checkbox. The post-2023 checkbox is a *feature* in the model, not a fix.

**FM-02 (CAVEAT): Gift transactions can be informative.** Gifts (code G) are now reported on Form 4 with a 2-day deadline (per the 2022 amendments). Cline-Williamson (2017) document that insider gifts cluster before negative news. Treat gifts as a separate channel, not a noise category.

**FM-03 (CAVEAT): Exercise-and-hold combined with M/F codes.** Mechanical, low information; the M/F codes must be filtered out before opportunistic classification.

**FM-04 (CAVEAT): Family-trust transfers below disclosure threshold.** Largely invisible; mitigation is to treat indirect ownership as part of the household-level rollup so that *disclosed* indirect activity is captured.

**FM-05 (CAVEAT): Options grant timing manipulation.** The "spring-loading" / "bullet-dodging" literature; less acute post-SOX but still nonzero. Suppress option-grant transactions from the action vector.

**FM-06 (CAVEAT): Restricted stock vesting cycle.** Mechanical; the routine/opportunistic filter handles this in expectation, but short-history executives leak vest events into the opportunistic bucket. Per-executive history depth (≥3 years) is a hard requirement before a trade can be classified.

**FM-07 (CAVEAT): Founder dilution / liquidity programs.** Bezos, Zuckerberg, Jobs-style large founders sell on schedule; their behavior is a structural negative control. Founder-blockholder weight = 0.15 in v0 reflects this; learned weight in v1 will refine.

**FM-08 (CAVEAT): Retirement-driven sales.** An executive announcing retirement systematically sells on a known schedule. Layer 2 should consume firm-level retirement / departure announcements and suppress trades within 12 months following.

**FM-09 (BLOCKER): Section 16(b) short-swing-profit rule.** Mechanically prevents profit-taking on offsetting trades within 6 months. The buy-side data is therefore conditional on insiders accepting a 6-month lockup. Does not invalidate the buy asymmetry but affects the interpretation. Document explicitly.

**FM-10 (BLOCKER): Tippee / shadow-insider trading.** See §9.2. Foundational caveat, not fixable.

**FM-11 (BLOCKER): Survivor bias in the say corpus.** See §9.3. Backtest must use a survivorship-bias-free panel.

**FM-12 (BLOCKER): Hindsight contamination from Q&A.** Analyst questions in earnings-call Q&A leak forward information from analyst networks into "executive" text. Layer 4 must separate prepared remarks from Q&A and tag the Q&A side for higher noise treatment. This is Thread C.

**FM-13 (CAVEAT): Cross-listed / ADR firms.** Foreign Private Issuers exempt from Section 16. Universe filter excludes non-US-domestic registrants.

**FM-14 (BLOCKER): Rule 144 affiliate sales.** Form 144 is a separate filing capturing large affiliate sales. Layer 2 must ingest Form 144 alongside Form 4. Now machine-readable post-April-2023 (EDGAR-only filing).

**FM-15 (CAVEAT): No-signal universe fraction.** Roughly 800–1200 firms in the Russell 3000 satisfy all Layer 2 prerequisites (≥3 years Form 4 history, sufficient earnings call coverage, US-domestic). The universe is smaller than the headline Russell 3000 and capacity claims must be scaled accordingly.

**FM-16 (BLOCKER): M&A target contamination.** Pre-deal opportunistic trades retroactively look like the strongest signal. Backtest must exclude the 30 days preceding any M&A announcement to avoid forward-contaminating training data.

**FM-17 (CAVEAT): Earnings call scheduling endogeneity (Niessner 2015).** Managers strategically time disclosures around plan windows. The "say" and "do" timestamps are not independently sampled. Granger-causality and lead-lag tests assume serial independence that is violated; do not use them naively.

**FM-18 (CAVEAT): Auditor resignation / 8-K item 4.02.** Mid-quarter information-environment resets. Layer 2 should consume 8-K item 4.02 events and treat sentiment data crossing such events as belonging to different quasi-quarters.

**FM-19 (CAVEAT): Index reconstitution.** Russell add/delete events drive abnormal flows that overlap with insider behavior; control for index-membership change in $\mathbf{x}$.

**FM-20 (CAVEAT): SPAC sponsors.** De-SPAC sponsor trading on the new vehicle has different economics than ordinary insider trading. Either suppress or treat as a separate role bucket.

**FM-21 (CAVEAT): Late filings.** Biggerstaff-Cicero-Wintoki document ~8% delinquent filings post-SOX, clustering in high-information-asymmetry periods. Late-filed trades may be the *most* informative subset. Keep them; do not drop on as-of-date join failures.

**FM-22 (CAVEAT): Year-end (12/31) gift and tax-loss clustering.** Real but second-order; observable as December peaks in firm-level gift/sale clusters.

---

## 11. Validation

### 11.1 Validation framework

Layer 2 is a Bayesian state estimator, not a return-prediction factor. Its validation has three tiers, in order of priority:

1. **Synthetic-data identifiability and recovery** — the primary v1 criterion. Run the harness in §11.2 and verify that on data drawn from a known generating process, the estimator recovers the latent state, the posterior, and the parameters within the documented threshold table. This is the criterion the v1 release must clear.
2. **Posterior calibration against SEC-enforcement labels** — the v1.1 calibration criterion, deferred until Thread B closure produces the labeled dataset.
3. **Predictive validity** — conditional on the posterior, does the layer carry information about future returns net of standard quant factors? This is the long-run validation tier; Layer 2 is useful even at zero alpha if the posterior is well-calibrated, because it conditions other layers.

### 11.2 Synthetic-data validation (primary v1 criterion)

The committed specification is rejected if synthetic-data recovery fails the threshold table in `docs/layers/layer_2/research/Insider Divergence Detection as Bayesian HMM Spec with Covariate-Dependent Emission.md` §4.3.3. Validation is performed by running

```
cd experiments/layer_2/hmm_validation_v0
python run.py --seed 20260426
```

and verifying that the output `outputs/results.md` reports PASS on all eight threshold rows: Hamming rate ≤ 0.20 on the switching cohort, ≤ 0.10 on the always-T and always-C cohorts; ECE ≤ 0.08; RMSE on emission means ≤ 0.15; Frobenius RMSE on the transition matrix ≤ 0.20; multi-start agreement fraction ≥ 0.40; and mean posterior entropy ≤ $0.55 \log 2 = 0.38$. Robustness sweeps at $\beta_{\text{sell}} = 0.6$ and channel-availability $a^{(c)} = 0.3$ extend the pass criterion to Hamming ≤ 0.30 in those degraded regimes. The harness is the v1 release gate; a release cannot ship if the harness fails any threshold.

#### Known limitations of v0 harness execution

The v0 harness validates a *tractable approximation* of the §4 specification, not the specification as committed. The audit at `experiments/layer_2/hmm_validation_v0/audit.md` enumerates the gaps row by row; the major ones are the skew-normal narrative emission (replaced by Gaussian in v0), the full $g_\delta \cdot g_s \cdot g_\kappa \cdot g_o \cdot g_\pi$ multi-component action emission (reduced to a Bernoulli sell and a Bernoulli opportunistic flag in v0), and the hierarchical Type-II ML outer loop (replaced by per-executive fits with a fixed prior in v0). Validation as currently executed therefore demonstrates that the *family* of HMMs the §4 specification belongs to is identifiable and recoverable on synthetic data; it does not yet demonstrate that the *specifically committed* §4 HMM is identifiable and recoverable.

A v1 harness expansion is required before this document can claim the full §4 specification is empirically validated. The v1 harness expansion will live at `experiments/layer_2/hmm_validation_v1/` (to be created when work begins). Until v1 exists, this document does not claim full-specification validation.

The v0 harness execution against `--seed 20260426` completed end-to-end in 1185.2 seconds (≈19.75 minutes) on a single core in the user's environment, modulo a single numpy-2.x compatibility fix documented in `experiments/layer_2/hmm_validation_v0/notes.md`. The harness ran cleanly. The threshold-validation result, however, **fails five of eight rows at the default sweep point** — the three Hamming metrics, the ECE, and the emission-mean RMSE all miss the §4.3.6 expected values by deltas an order of magnitude larger than the documented Monte Carlo tolerance (±0.02 on Hamming/ECE, ±0.05 on RMSE). The transition-matrix Frobenius RMSE, the multi-start convergence fraction, and the mean posterior entropy reproduce within tolerance. The pattern is consistent across all nine sweep cells; Hamming on the switching cohort lies in [0.257, 0.335] across the full grid, with no cell within ±0.10 of the 0.14 expected value.

The threshold-failure pattern — transition kernel and convergence diagnostics OK, state-recovery and emission-recovery off — is informative about where to look. The leading hypothesis is the action-channel availability prior, which the harness hard-codes to $\sigma(0.0) = 0.50$ in state $T$ and $\sigma(-1.4) \approx 0.20$ in state $C$, against the generator's `Bernoulli(0.4)` and `Bernoulli(0.2)`. This row was already flagged severity DEVIATION in `audit.md` on theoretical grounds; the threshold-failure result elevates it to *the proximate-cause candidate*. Other candidates — the un-fitted covariate slope `beta_x` on the sell-direction logit, and the possibility that the §4.3.6 expected values were never verified against the §4.3.4 code — are documented in `experiments/layer_2/hmm_validation_v0/notes.md` and `STATUS.md`.

The implication for the v0.2 design document is direct. Synthetic-data validation is the primary v1 criterion (§11.2). The v0 harness fails it. The v0.2 specification is therefore *committed but not yet empirically validated*; v1 release is gated on root-causing the threshold failures and either fixing the harness or establishing that the §4.3.6 expected values were the source of the mismatch. The v1 harness work item gains a new sub-task: investigate the threshold failures before expanding the model. The audit's catalogue of spec-vs-harness gaps is now also the hypothesis space for the failure investigation; v1 should not assume the gaps are independent of the failure.

### 11.3 Calibration validation against SEC-enforcement labels (v1.1, deferred)

Calibration against external labels is the second validation tier and is deferred to v1.1 pending Thread B closure. Once labels are available, calibration is tested with positive labels drawn from SEC enforcement actions (AAERs, litigation releases) where the labeled time window is the 24 months prior to the enforcement action; negative labels drawn from firm-quarters with no subsequent enforcement, restatement, or material adverse event within 36 months, matched to positive cases on size, industry, and time period; and reliability-diagram, ECE, and Brier-score metrics applied to the held-out posterior.

A well-calibrated Layer 2 has posterior values that match observed concealment frequencies in held-out data. A posterior that says 80% concealing should be right roughly 80% of the time. This is the criterion that, when achieved, lifts Layer 2 from "synthetic-validated" to "label-validated" status; until Thread B closes, the v1 validation claim is restricted to synthetic recovery.

### 11.4 Predictive validity (long-short backtest)

If and only if synthetic-recovery and calibration validation both pass, predictive validity is tested via:

- **Universe:** ~800–1200 firms passing the Layer 2 filter cascade (§9.3).
- **Train period:** post-SOX through end of 2018.
- **OOS-1:** 2019–2022 (pre–10b5-1 reform).
- **OOS-2:** 2023 onward (post-reform; tests regime stability).
- **Walk-forward:** annual reweighting of role weights and any HMM hyperparameters; no peeking on regime breaks.
- **Filing-date discipline:** trades enter the signal at filing date, not transaction date, to avoid look-ahead bias. The Ozlen-Batumoglu (2025) finding that 70–80% of total alpha dissipates between transaction and filing must be reflected in honest gross-alpha expectations.
- **Survivorship bias:** CRSP-style panel including delisting returns (−30% convention for performance-related delistings).
- **Cost model:** bid-ask (TAQ-based monthly proxy), market impact (small-cap-calibrated Almgren-Chriss), borrow cost on the short side (Markit Equity Lending via WRDS where available).
- **Multiple comparisons:** Benjamini-Hochberg FDR at q=0.05 across all parameter cells (role weights × event window × industry × regime).
- **t-statistic threshold:** **t > 3.0 net of costs and after BH-FDR** is the minimum acceptable for any "validated" claim. Harvey-Liu-Zhu (2016) is the standard reference; t > 3.0 is the lower bound; t > 3.5 is preferred given that Layer 2 is a follow-on factor on a known anomaly. Anything below this is reported as "exploratory."

### 11.5 What "alpha" means in expectation

The honest expectation, given everything in §3 and §11.4:

- Cohen-Malloy-Pomorski (2012) headline: 82 bps/month value-weighted, 180 bps/month equal-weighted.
- McLean-Pontiff (2016) post-publication decay: average 58%.
- Ozlen-Batumoglu (2025) filing-date alpha loss: 70–80% of transaction-date alpha.
- Cost-of-trade haircut on small-cap names: 20–40 bps round-trip.

Stacking these multiplicatively, a *realistic* gross-alpha expectation for a CMP-style replication on filing-date data, post-publication, post-cost, is in the **5–20 bps/month range**, which translates to a Sharpe in the 0.3–0.7 band — not directly tradeable as a standalone strategy. This is *not* Layer 2's validation claim. Layer 2's primary validation claim is synthetic-data identifiability and recovery (§11.2); calibration against external labels is the v1.1 secondary claim (§11.3); any predictive alpha is a tertiary bonus.

This is the framing the design doc commits to. Anything stronger requires evidence Layer 2 has not yet produced.

### 11.6 Sanity checks

In addition to formal validation, Layer 2 must reproduce four well-known patterns as sanity checks (these are *not* validation, only verification that the implementation is not broken):

- **Enron, 2000–2001:** insiders sold heavily into bullish public statements pre-collapse. Posterior should be elevated for relevant executives in the 12–18 months prior.
- **HealthSouth, 2002–2003:** Scrushy and inner circle traded against bullish guidance. Same expectation.
- **Buffett (Berkshire Hathaway):** positive control. Buffett's purchases and statements are aligned; posterior should be near-baseline.
- **Bezos / Zuckerberg founder sales:** negative control. Heavy sales pursuant to long-standing 10b5-1 plans; posterior should *not* be elevated despite the high $|d|$.

A Layer 2 implementation that does not reproduce all four sanity-check patterns is broken. A Layer 2 implementation that reproduces all four is not yet validated — sanity checks are necessary but not sufficient.

---

## 12. Cross-layer integration

### 12.1 Identifier scheme

Layer 2 commits to the following canonical identifiers:

- **Firm:** SEC CIK (immutable). Joined to ticker via the SEC company-tickers JSON, with awareness that CIK-to-ticker is many-to-many over time (mergers, ticker changes, delistings). PERMNO from CRSP is the canonical security identifier for backtests, joined to CIK via WRDS link tables when WRDS is available.
- **Executive:** SEC reporting-person CIK (stable across firms; executives keep their CIK when they switch jobs). This is the right key for within-executive analysis and for tracking executive careers across firms.
- **Household:** firm CIK + executive CIK + indirect-ownership filings rolled up via name + relationship + (optionally) address heuristic match. The household is the unit at which trading is aggregated to handle spousal / family-trust filings as a single economic actor.
- **Time:** UTC timestamp at filing event. Filing date and transaction date are both retained on every record; downstream consumers must use filing date for tradeable applications.

### 12.2 Provenance schema

Every Layer 2 record carries:

```
provenance: {
  source_filing_acc_nums: [str],   # SEC accession numbers
  source_filing_urls: [str],       # canonical EDGAR URLs
  upstream_layer4_version: str,    # Layer 4 sentiment model version
  upstream_layer1_version: str|null,
  layer2_model_version: str,       # this layer
  parser_version: str,             # edgartools or alternative
  computed_at: timestamp,
}
```

Without provenance, backtests are not reproducible and design choices are not auditable. This is non-negotiable.

### 12.3 Contract with Layer 4

Layer 4 must deliver:

- Per-call, per-speaker sentiment scores for earnings calls (CEO prepared, CEO Q&A, CFO prepared, CFO Q&A, other-speaker).
- Per-press-release sentiment (firm-aggregated).
- Per-8-K-event sentiment (with item-number tag for filtering).

Speaker attribution is the gating capability. Until Layer 4 produces speaker-attributed output (Thread C), Layer 2 runs in a degraded mode using firm-aggregated sentiment, which loses the per-executive resolution that is the core asset.

### 12.4 Contract with Layer 1 (anticipated)

Layer 1, when implemented, must deliver:

- Per-filing risk-factor language drift score (Lazy Prices–style cosine distance to prior filing).
- Per-filing sentiment (10-K/Q tone, separately for MD&A and risk factors).
- Per-8-K event tone.

Layer 2 will integrate these as channels 6–8 in the observation vector. Until Layer 1 is implemented, Layer 2 runs without these channels and the posterior is correspondingly less informative.

### 12.5 What downstream consumers see

A consumer of Layer 2 (Layer 5, an analytical UI, a future product) sees only the schema in §4.9. They must not depend on the HMM internals, channel weights, role-weight calibration, or any Layer-2-internal state. If a downstream consumer would benefit from richer access, the right move is to expose additional fields in the schema, not to bypass the contract.

---

## 13. The market-reception layer (deferred)

A separate architectural commitment that emerged from discussion of Layer 2 but is *not* part of Layer 2: a future layer that estimates **how the investor population is currently receiving the firm's narrative**.

The intuition: companies actively manage public image. They produce narrative under pressure (from short-sellers, activists, regulators, the press) and measure their success through investor response. The investor population is not a single rational receiver — it is a heterogeneous flock with varying credibility-weights, response speeds, and susceptibility to narrative pressure. The dynamics resemble multi-predator-on-flock systems studied formally in mathematical biology (Strömbom et al. 2014) and informally in heterogeneous-agent finance (Lux-Marchesi 1999, Cont-Bouchaud 2000, Hong-Stein 1999, the Brock-Hommes adaptive belief systems literature).

This is not Layer 2. Layer 2 is firm-internal: is *this executive* currently concealing? The market-reception layer is cross-sectional: is *the investor population* currently buying the story? The two compose: firms where Layer 2 says "concealing" and the market-reception layer says "buying the story" are exactly where the divergence matters — that is the gap a strategy could exploit.

The architectural commitment is to *reserve the slot* for this layer and to enumerate the observation channels it would consume:

- Cross-sectional dispersion of analyst estimates (sell-side estimate dispersion and revisions).
- Short interest as % of float, plus short-interest momentum, plus borrow utilization (Boehmer-Jones-Zhang 2008, Engelberg-Reed-Ringgenberg 2012).
- Options-implied dispersion: skew, vol-of-vol, put-call open-interest ratio (Hao-Li 2021).
- Institutional ownership concentration (Herfindahl over 13F filers).
- Retail flow proxies (Robinhood-era retail-attention indices; Reddit/StockTwits sentiment volatility).
- Narrative cadence: count of firm-originated communications per quarter normalized by firm size.
- Narrative effort intensity: word count of external comms per quarter.
- Sell-side initiation/upgrade/downgrade flow.

The interaction the layer would estimate is between *narrative effort* and *fundamental performance*: firms working hard to maintain a story while fundamentals don't justify it are the regime where insider divergence would also be expected to be highest. This is the formal channel through which the public-image-maintenance intuition enters the platform.

The discipline this commitment imposes: **before any simulation-based or agent-based version of this layer is built, a non-simulation baseline must be tested first**. Compute the listed channels directly from data; combine them into a market-reception-state estimate via a simple weighted aggregation; validate against future-return realizations and against Layer 2's posterior. If the simple weighted version explains the relevant variance, agent-based simulation buys nothing. If it does not, simulation may be justified — but only in light of what's been ruled out.

This layer is deferred; its formal specification is a future research thread separate from Layers 1–4.

---

## 14. Adversarial robustness

If Layer 2 becomes well-known, executives will adapt. The 2022 10b5-1 reform is an existence proof: Divakaruni-Hvide-Tveiten (2026) document that the reform did not reduce insider abnormal returns; insiders shifted opportunistic trading toward the rule's margin.

Likely adaptation paths over a 5-year horizon:

- More tippee trading (relatives, networked directors, sell-side analysts) to keep informed flow off Form 4 entirely.
- More "language laundering" — outside spokespeople, IR consultants, and third-party analysts deliver tone the executive cannot say directly. This bypasses speaker-attributed sentiment.
- More structured / derivative compensation (collars, prepaid variable forwards) achieving economic sale without an S-coded transaction.
- More non-equity wealth diversification — private investments, real estate, family offices — allowing executives to act on private information without trading firm equity.
- Strategic dampening of earnings-call language: "low-content quarterly" reduces signal in either direction.

Implication: Layer 2 cannot be deployed as a frozen model. The HMM transition matrix, role weights, and channel-emission parameters must be online-learned with drift detection. Deployment includes a monitoring layer that flags when emission distributions shift outside training-time bounds, and when role-weight learners begin to overfit recent labels.

This is documented as a v2 requirement; v1 may ship with periodic recalibration only. But the architecture must allow online learning to be added without restructuring the layer.

---

## 15. Operations

### 15.1 Cold-start

A new executive's per-executive posterior beats the role-pooled prior — in expected log-loss on held-out observations — once $T_i \ge 18$, the empirical break-even at the default sweep point in the v0 harness. Below this threshold, the role-pooled posterior $\Pr(z = C \mid r(i), \iota(i))$ is reported instead, with an explicit `cold_start = True` flag in the Layer 2 output schema (§4.9). Cold-start is automatic; no human-in-the-loop trigger is required, and the threshold is a configuration parameter that may be re-fit when the v1 harness expansion produces a tighter estimate.

### 15.2 Online updating

Two-mode update strategy when a new observation $y_{i, T+1}$ arrives. The cheap path runs one forward step on the existing $\log \alpha_T$, produces $\log \alpha_{T+1}$ and the filtered $\Pr(z_{T+1} \mid y_{1:T+1})$ at $O(K^2)$ cost per executive, and is used for live divergence-score broadcasts. The expensive path re-runs full forward-backward smoothing on $y_{1:T+1}$ at $O(K^2 (T + 1))$ cost and is performed nightly at the universe level; the smoothed result overwrites the filtered estimate. Per-executive parameters $\theta_i$ are not re-estimated on every observation. Re-estimation is triggered by the quarterly outer-loop hyperparameter refit, or by an ad-hoc concept-drift alarm when the executive's accumulated forward log-likelihood drift $\ell_t - \ell_{t-1}$ deviates by more than $3\sigma$ from its historical mean.

### 15.3 Recalibration triggers

Hyperparameters $\Phi$ are refit quarterly on the full universe. Off-cycle refit is triggered by any of the following: a regulatory regime change — for example, any further SEC 10b5-1 amendment, or an analogous structural break in Form 4 disclosure rules; population-level posterior-calibration ECE on hold-out exceeding 0.10; or universe-mean posterior entropy rising above $0.45 \log 2 = 0.31$. Each refit produces a versioned snapshot $(\Phi^{(v)}, \theta_i^{(v)})$ for reproducibility and counterfactual analysis. Backtest re-runs always use the as-of-date hyperparameters, never the current snapshot.

### 15.4 Compute-budget estimates

At full scale — $N = 1000$ executives × 80 quarterly refits over a 20-year backtest — single-core wall-clock is roughly 5 hours on a 32-core node, with peak memory of roughly 80 GB for the forward-backward state arrays. Mitigations available if the budget is prohibitive: reduce multi-start to $K = 5$ with adaptive expansion to $K = 20$ only on flagged executives; sparse-state pruning (drop states with posterior occupancy below 5); cache emission-likelihood tensors across outer-loop iterations for roughly 30% speedup; or move to GPU with `cupy.scipy.special.logsumexp` for the outer loop, roughly a 10× speedup at the cost of one engineer-week of implementation work.

### 15.5 Deferrals

The following commitments are explicitly deferred to v1.x or v2 of Layer 2, each with a documented trigger condition. The deferral is itself a design commitment: until the trigger fires, the v1 specification is what ships, and the deferred element is *not* a hidden TODO that blocks v1 — it is a known limitation whose acceptability is documented here.

Full Bayesian MCMC inference over $(\Phi, \theta_i)$ is deferred to v1.x. The v1.0 estimator uses Type-II ML empirical-Bayes for tractability. The trigger for promoting MCMC to v1.x is the discovery, during v1 deployment, of pathologies in the empirical-Bayes posterior that MCMC would resolve — for example, posterior bimodality on $\eta_i$ that the Laplace approximation misses, or boundary-pinning of $\tau$ in the half-Cauchy hyperprior.

Semi-Markov durations are deferred to v2. The trigger is the geometric-bias test from §4.6, which compares a geometric-duration estimator against ground-truth negative-binomial-duration synthetic data: if regime-recovery Hamming-rate degrades by more than 0.04 when the duration distribution is mis-specified, semi-Markov is reopened.

Continuous-time HMM is deferred to v2. The trigger is observation-cadence change: if Form 4 filing latency or earnings-call cadence becomes irregular enough that discrete weekly bucketing introduces material aliasing — for example, post-EDGAR-Next filing-latency distributional shift — CT-HMM is reopened.

Full multi-component skew-normal action emission, with the size, code, opportunistic, and 10b5-1 components all jointly fitted, is deferred to v1.1 inside the v1 harness expansion track. The current v0 harness fits a Bernoulli direction and a Bernoulli opportunistic flag only. The trigger for the full action emission is the v1 harness expansion under Thread A v1.

Hierarchical Type-II ML in the executable harness is deferred to v1. The current v0 harness fits each executive against a fixed shared prior, not a role-level hierarchy with an outer EB loop. The trigger for hierarchical Type-II ML in the harness is the v1 harness expansion; the design-document commitment to it remains §4.6.

## 16. Versioning and update policy

Layer 2 model versions follow semantic versioning:

- **v0.x** — prototyping; hand-set role weights; no production claim.
- **v1.0** — minimum production-eligible; learned role weights from Thread B; calibration-validated; Layer 4 speaker-attributed; full provenance schema.
- **v1.x** — incremental improvements; new channels from Layer 1 once available; refined controls.
- **v2.0** — continuous-state HMM; online-learning; market-reception-layer integration.

Every version increment requires:

1. Updated documentation in this file.
2. Calibration re-validation against held-out enforcement labels.
3. A backward-compatibility statement: do downstream consumers need to update?
4. A changelog entry.

Schema changes (the §4.9 record format) are major version bumps. Internal recalibrations that do not change the schema are minor or patch versions.

---

## 17. Open research threads

The following research threads track work whose completion advances Layer 2's specification or unblocks downstream design. The Thread vocabulary is internal to the design document — it is not the same as the experimental scaffolding under `experiments/`, which tracks code-and-numbers work.

### Thread A — Mathematical formalization of the divergence operator

**Status:** Specification complete (this document §4); v0 validation harness complete at `experiments/layer_2/hmm_validation_v0/`; harness expansion to full §4 specification deferred to Thread A v1.

**Goal (achieved at v0.2):** Derive the formal Bayesian-state-estimator specification with argued identifiability under realistic data conditions; compare the hierarchical HMM to alternatives (residualized regression, mutual information, conditional probability ratio, linear-Gaussian state-space); stress-test on synthetic data where the true generating process is known. The §4 specification is now committed; the harness `run.py` exists and validates the family containing the spec. The remaining work is the v1 harness expansion, which closes the gaps catalogued in `experiments/layer_2/hmm_validation_v0/audit.md` — skew-normal narrative emissions, full multi-component action emission, hierarchical Type-II ML outer loop, and per-executive identifiability flagging into the output schema. Thread A v1 is parallel to Thread B and does not block it.

**Estimated effort for v1:** Roughly 8–14 hours, dominated by the action-emission expansion and the Type-II ML outer loop.

**Dependency note:** Threads B, C, D, and E are unblocked at the spec level by Thread A's closure. Thread B's training target and feature construction now reference the §4 specification; Thread C's speaker-attribution output schema is what feeds the per-channel sentiment $s_t^{(c)}$ at $c \in \{1, 2, 3, 4\}$; Thread D's cost-calibrated divergence-to-action mapping consumes the §4.9 output schema; Thread E's Layer-1/Layer-2 channel contract is the §4.3 channel table at $c \in \{6, 7\}$.

### Thread C — Speaker-attributed Layer 4

**Status:** Blocking for v1; Layer 4 scope but coupled to A.

**Goal:** Extend Layer 4 to produce per-speaker sentiment from earnings call transcripts. Investigate transcript sources accessible to the project (FactSet CallStreet, Refinitiv eikon, AlphaSense via student access, MotleyFool's free archives). Establish realistic accuracy of CEO-vs-CFO-vs-analyst attribution. Replace FinBERT with FinLlama or a Llama-3.1-8B fine-tune for sentiment scoring; benchmark against current Layer 4.

**Estimated effort:** 6–10 hours including data-source investigation.

**Why with A:** A's output schema depends on what C can deliver per executive. Run them in parallel rather than sequentially.

### Thread B — SEC-enforcement-labeled supervised pipeline

**Status:** Blocking for v1; depends on A.

**Goal:** Build the labeled dataset from SEC AAERs, litigation releases, and accounting restatements following Ali-Hirshleifer (2017) protocol. Define positive/negative label criteria, label-window construction, false-negative-rate expectations, time-lag handling between trade and enforcement, survivorship handling for enforcement-action firms themselves. Train role-weight classifier; produce the v1 learned role weights.

**Estimated effort:** 6–10 hours.

**Why after A:** B's training target and feature construction depend on A's specification of what the operator's inputs are.

### Thread D — Cost-model calibration

**Status:** Deferrable; can be inline during v1 prototype.

**Goal:** Pull bid-ask spreads (TAQ via WRDS or Compustat-based monthly proxy), market impact (Almgren-Chriss with small-cap calibration), borrow costs (Markit Equity Lending). Produce a per-trade cost-model function used in §11.4 backtests.

**Estimated effort:** 4 hours.

**Why later:** Cost calibration matters only when there is a v1 alpha number to deflate. Inline during prototype is fine.

### Thread E — Layer-1 / Layer-2 cross-layer integration

**Status:** Deferrable until Layer 1 begins design.

**Goal:** Specify the observation-channel contract Layer 1 will satisfy when implemented. Define the temporal alignment, identifier mapping, and provenance schema between Layer 1 outputs and Layer 2 inputs.

**Estimated effort:** Architectural; ~3 hours of writing once Layer 1 begins.

**Why last:** No work to do until Layer 1 is being designed.

### Logical conduct order

With Thread A's specification closed at v0.2, the right order for remaining work is:

1. Thread A v1 (harness expansion) and Thread C in parallel; A v1 is no longer gating because the spec is committed and the v0 harness validates the family the spec belongs to, but it is the work that lifts validation from "family" to "specifically committed model."
2. Thread B after Thread C, since B's labels feed the role-weight learner whose features are partly Thread-C-derived.
3. Thread D inline during prototype, since D needs prototype outputs to deflate.
4. Thread E when Layer 1 begins, since E is interface-design blocked on Layer 1's existence.

Each thread produces its own working document; findings are integrated into this document as a version increment. Layer 2 v1.0 follows completion of Threads A v1, B, and C with D inline; v1.x adds E once Layer 1 is in place.

---

## 18. References

### Primary literature

- Cohen, L., Malloy, C., & Pomorski, L. (2012). Decoding Inside Information. *Journal of Finance*, 67(3), 1009–1043.
- Lakonishok, J. & Lee, I. (2001). Are Insider Trades Informative? *Review of Financial Studies*, 14(1), 79–111.
- Jeng, L., Metrick, A., & Zeckhauser, R. (2003). Estimating the Returns to Insider Trading: A Performance-Evaluation Perspective. *Review of Economics and Statistics*, 85(2), 453–471.
- Seyhun, H. N. (1998). *Investment Intelligence from Insider Trading*. MIT Press.
- Ali, U. & Hirshleifer, D. (2017). Opportunism as a firm and managerial trait: Predicting insider trading profits and misconduct. *Journal of Financial Economics*, 126(3), 490–515.
- Wang, W., Shin, Y.-C., & Francis, B. B. (2012). Are CFOs' Trades More Informative Than CEOs' Trades? *Journal of Financial and Quantitative Analysis*, 47(4), 743–762.
- Knewtson, H. & Nofsinger, J. (2014). Why are CFOs more informed than CEOs?
- Cohen, L., Malloy, C., & Nguyen, Q. (2020). Lazy Prices. *Journal of Finance*, 75(3), 1371–1415.
- Kothari, S. P., Shu, S., & Wysocki, P. (2009). Do Managers Withhold Bad News? *Journal of Accounting Research*, 47(1), 241–276.
- Niessner, M. (2015). Strategic Disclosure Timing and Insider Trading.

### Recent / contested-direction literature on the 2023 reform

- Divakaruni, A., Hvide, H. K., & Tveiten, A. (2026). Insider trading and the 10b5-1 reform. CEPR DP 21199.
- Chung, K. H. & Chuwonganant, C. (2026). Effects of 10b5-1 amendments on insider trading and market quality. SSRN 6409618.
- Columbia CLS Blue Sky working paper (2025). Insider Trading After the 2022 Rule 10b5-1 Amendment.

### Decay and validation framework

- McLean, R. D. & Pontiff, J. (2016). Does Academic Research Destroy Stock Return Predictability? *Journal of Finance*, 71(1), 5–32.
- Hou, K., Xue, C., & Zhang, L. (2020). Replicating Anomalies. *Review of Financial Studies*, 33(5), 2019–2133.
- Harvey, C. R., Liu, Y., & Zhu, H. (2016). … and the Cross-Section of Expected Returns. *Review of Financial Studies*, 29(1), 5–68.
- Ozlen, M. & Batumoglu, S. (2025). The Death of Insider Trading Alpha: Most Returns Occur Before Public Disclosure. SSRN 5966834.

### NLP / sentiment

- Araci, D. (2019). FinBERT: Financial Sentiment Analysis with Pre-trained Language Models. arXiv:1908.10063.
- Konstantinidis, T., et al. (2024). FinLlama: Financial Sentiment Classification for Algorithmic Trading. arXiv:2403.12285.
- Loughran, T. & McDonald, B. (2011). When Is a Liability Not a Liability? *Journal of Finance*, 66(1), 35–65.

### Market-reception / heterogeneous agents (deferred layer)

- Strömbom, D., et al. (2014). Solving the shepherding problem. *Journal of the Royal Society Interface*, 11(100).
- Lux, T. & Marchesi, M. (1999). Scaling and criticality in a stochastic multi-agent model of a financial market. *Nature*, 397, 498–500.
- Cont, R. & Bouchaud, J.-P. (2000). Herd behavior and aggregate fluctuations in financial markets. *Macroeconomic Dynamics*, 4(2), 170–196.
- Hong, H. & Stein, J. (1999). A unified theory of underreaction, momentum trading, and overreaction in asset markets. *Journal of Finance*, 54(6), 2143–2184.
- Hommes, C. (2006). Heterogeneous Agent Models in Economics and Finance. In *Handbook of Computational Economics* Vol. 2, Ch. 23.
- DeMarzo, P., Vayanos, D., & Zwiebel, J. (2003). Persuasion bias, social influence, and unidimensional opinions. *Quarterly Journal of Economics*, 118(3), 909–968.
- Boehmer, E., Jones, C., & Zhang, X. (2008). Which Shorts Are Informed? *Journal of Finance*, 63(2), 491–527.
- Hao, Q. & Li, K. (2021). The informed options trading and corporate insider trading. *Financial Review*, 56(2).

### Data sources

- Balogh, A. (2023). Forms 3, 4, 5: A comprehensive insider transaction dataset. *Scientific Data*, Nature.
- Gunning, D. *edgartools* (Python library), v5.x. https://github.com/dgunning/edgartools
- SEC EDGAR Developer Resources. https://www.sec.gov/about/developer-resources

---

*Document version: v0.2. Last updated: April 26, 2026. Next update on completion of Thread A v1 (harness expansion) or Thread B (SEC-enforcement-labeled supervised pipeline), whichever closes first.*

---

## Changelog

**v0.2 — April 26, 2026.** Integration of Thread A. §4 replaced in full with the committed two-state hierarchical HMM with covariate-dependent emissions; the model section now contains the formal state space, the hierarchical multinomial-logit transition kernel with role-level pooling, the skew-normal narrative emission and the multi-component action emission, the discrete weekly time discretization with MAR narrative missingness and informative absence on the action channel, the Type-II ML EM procedure, the latent-confounder demonstration, and the I1–I8 identifiability conditions including the binding I6 non-absorption constraint. §3.2 now carries a forward-pointer to §4.7 for the formal latent-confounder argument. §11 has been restructured: the v0 synthetic-data harness at `experiments/layer_2/hmm_validation_v0/` is the primary v1 validation criterion; SEC-enforcement-label-based calibration is moved to v1.1 calibration, deferred to Thread B closure; a "Known limitations of v0 harness execution" subsection states explicitly that the v0 harness validates a tractable approximation of the §4 specification rather than the specification itself, and that v1 harness expansion is required before the document can claim full-specification empirical validation. §4.9 (output schema) extends with cold-start, identifiability, and post-2023-regime fields. §15 (Operations) is new, covering cold-start logic, online updating, recalibration triggers, and compute-budget estimates, plus an explicit Deferrals subsection cataloguing v1.x and v2 deferrals with documented trigger conditions. §16, §17, and §18 are renumbered to make room. §17 marks Thread A as specification complete with v1 harness expansion deferred; Threads B, C, D, and E are unblocked at the spec level. Harness executed end-to-end against `--seed 20260426` in 1185.2 s; outcome is NUMBERS_DIFFER, with five of eight thresholds failing against the §4.3.6 expected-output table. The §11.2 limitations subsection reports the failure honestly and identifies the action-availability prior calibration mismatch as the leading proximate-cause candidate.

**v0.1 — April 26, 2026.** Initial architectural commitment.
