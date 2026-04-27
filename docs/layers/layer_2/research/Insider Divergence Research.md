# Layer 2: Insider Divergence — Research Notes for the Narrative Atlas Founding Memo

These notes synthesize a deep literature, mechanism, data, technique, validation, and failure-mode pass to support the formal Layer 2 design document. Inline citations link to primary sources (papers, SEC documents, library docs, data-provider sites). Where literature genuinely disagrees or remains open, that is flagged explicitly.

---

## 1. Literature Pass — Insider Trading Signal Research

### 1(a) Foundational Papers

**Jeng, Metrick, Zeckhauser (2003), "Estimating the Returns to Insider Trading: A Performance-Evaluation Perspective," Review of Economics and Statistics 85(2): 453–471.**
This is the canonical reference for whether insiders earn abnormal returns at the individual-trader level (not just the informativeness-to-outsiders question). Using a comprehensive sample of reported insider transactions from 1975–1996 across NYSE/AMEX/Nasdaq, the authors construct value-weighted "rolling purchase" and "rolling sale" portfolios and evaluate them with Carhart-style four-factor performance methodology. The headline finding: insider **purchases earn risk-adjusted abnormal returns of more than 6% per year** (about 50–68 basis points/month for the first six months, with ~25% of the abnormal return arriving in the first five days and ~50% within the first month), while **insider sales do not earn statistically significant abnormal returns**. They also estimate the cost of insider trading to non-insiders at roughly 10 cents per $10,000 transaction. Remains foundational; the asymmetry between buys and sells is the bedrock of any modern insider-trading signal. ([SSRN](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=146029); [MIT Press](https://direct.mit.edu/rest/article-abstract/85/2/453/57400/); [2iQ summary](https://www.2iqresearch.com/blog/profiting-from-insider-transactions-a-review-of-the-academic-research))

**Cohen, Malloy, Pomorski (2012), "Decoding Inside Information," Journal of Finance 67(3): 1009–1043.**
The single most important methodological contribution to the modern insider-signal literature. Premise: insiders trade for many reasons (diversification, liquidity, taxes), not just on private information. The authors classify any insider with three consecutive years of trades in the same calendar month as a **routine trader**; everyone else's trades are flagged **opportunistic**. On 1989–2007 data, a portfolio strategy focused only on opportunistic trades earns **value-weighted abnormal returns of 82 bps/month (~10%/year)**, equal-weighted 180 bps/month, while routine trades earn essentially zero abnormal returns. Opportunistic trades also predict future firm-specific news (earnings forecasts, analyst forecasts, management guidance) and are disproportionately associated with later SEC enforcement. The most informed opportunistic traders are local non-senior insiders at geographically concentrated, poorly governed firms. Remains the canonical filter; every modern Form-4 signal pipeline includes some variant. ([NBER w16454](https://www.nber.org/papers/w16454); [Wiley/JOF](https://onlinelibrary.wiley.com/doi/abs/10.1111/j.1540-6261.2012.01740.x); [AQR summary](https://www.aqr.com/Insights/Research/Journal-Article/Decoding-Inside-Information); [HBS](https://www.hbs.edu/faculty/Pages/item.aspx?num=40609))

**Lakonishok and Lee (2001), "Are Insider Trades Informative?" Review of Financial Studies 14(1): 79–111.**
Comprehensive study of 1975–1995 insider activity across NYSE/AMEX/Nasdaq. Key findings: (i) insiders are aggregate contrarians but predict market movements better than naive contrarian strategies; (ii) **the predictive content is concentrated in purchases — sales have essentially no predictive ability**; (iii) cross-sectional predictability is driven by smaller firms; (iv) the difference between strong-buy and strong-sell portfolios (excluding 10%+ blockholders) is **about 4.8% in the first year** post-transaction; (v) market initially under-reacts at filing and the price drift accrues over the next ~6 months. Establishes the buy-vs-sell asymmetry that drives Layer 2's emphasis on directional weighting. ([Oxford Academic](https://academic.oup.com/rfs/article-abstract/14/1/79/1587398); [LSV PDF](https://www.lsvasset.com/pdf/research-papers/Insider-Trades-Informative.pdf))

**Seyhun (1986, 1992, 1998).**
Seyhun's body of work is the proximate origin of modern insider-trading empirics. The 1986 *Journal of Financial Economics* paper "Insiders' Profits, Costs of Trading and Market Efficiency" (16: 189–212) studied roughly 60,000 NYSE/AMEX transactions over 1975–1981 and found insiders systematically purchased before abnormal price increases and sold before abnormal declines, with abnormal returns of roughly +4.3% (purchases) and –2.2% (sales) over the first 300 days, controlling for size effects. The 1998 MIT Press book *Investment Intelligence from Insider Trading* documents that aggregate net insider activity over 1975–1989 explained up to ~60% of one-year-ahead market returns and that high-conviction CEO/officer trades dominate. ([2iQ overview](https://www.2iqresearch.com/blog/profiting-from-insider-transactions-a-review-of-the-academic-research); [MIT Press](https://mitpress.mit.edu/9780262692342/investment-intelligence-from-insider-trading/); [Insider Monkey](https://www.insidermonkey.com/insider-trading/education-center/academic-studies-on-insider-trading/3))

### 1(b) Recent State of the Art (2020+)

**Larcker, Lynch, Quinn, Tayan, Taylor (2021), "Gaming the System: Three 'Red Flags' of Potential 10b5-1 Abuse,"** Stanford Rock Center / Wharton working paper. First large-sample empirical look at 10b5-1 plan internals using a unique dataset of >20,000 plans, 10,123 executives at 2,140 firms, 55,287 sale transactions totaling **$105.3 billion** (Jan 2016–May 2020); average plan trade $1.9M. Identifies three abuse-correlated red flags: (1) short cooling-off periods, (2) single-trade plans, (3) plans adopted shortly before earnings. Trades under plans with **<30-day cooling-off had a subsequent industry-adjusted return of −2.5%; 30–60 days had −1.5%; >60 days, the loss-avoidance signal disappeared.** ~49% of plans were single-trade (median size $639K). This is the empirical foundation cited extensively in the SEC's 2021 proposed amendments. ([Harvard Corp Gov forum](https://corpgov.law.harvard.edu/2021/01/28/gaming-the-system-three-red-flags-of-potential-10b5-1-abuse/); [Stanford GSB](https://www.gsb.stanford.edu/faculty-research/publications/gaming-system-three-red-flags-potential-10b5-1-abuse); [Vega Economics summary](https://vegaeconomics.com/gaming-the-system-three-red-flags-of-potential-10b5-1-abuse))

**Kim, Kim, Rajgopal (2025), "Insider Trading After the 2022 Rule 10b5-1 Amendment,"** Columbia Business School Research Paper No. 5362431. Critical post-reform empirical paper. Pre-amendment, ~31.1% of 10b5-1 sales occurred within 90 days of plan adoption; post-amendment that fell to **1.7%**. Trades under amended plans are followed by **flat to slightly positive** subsequent returns vs. significantly negative pre-reform. So the reform empirically reduces opportunistic plan usage but at the cost of mildly worse price efficiency for affected firms. **Direct implication for Layer 2:** pre-2023 and post-2023 Form-4 data have materially different signal properties; treating them as one regime would be a methodological error. ([SSRN 5362431](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=5362431); [CLS Blue Sky summary](https://clsbluesky.law.columbia.edu/2025/07/31/insider-trading-after-the-2022-rule-10b5-1-amendment/))

**Ali and Hirshleifer (2017), "Opportunism as a Firm and Managerial Trait: Predicting Insider Trading Profits and Misconduct," Journal of Financial Economics 126(3): 490–515.** An advance over Cohen-Malloy-Pomorski: identifies opportunistic insiders by their **past profitability around quarterly earnings announcements**. Trades by past-profitable insiders earn 4-factor alphas of **>1%/month value-weighted**, significant on the short side (which CMP largely was not). Firms with opportunistic insiders also have higher rates of earnings management, restatements, SEC enforcement, shareholder litigation, and excess executive comp — opportunism is a domain-general trait, not a one-off. ([RePEc](https://ideas.repec.org/a/eee/jfinec/v126y2017i3p490-515.html); [UCI/Hirshleifer](https://sites.uci.edu/dhirshle/abstracts/opportunism-as-a-managerial-trait-predicting-insider-trading-profits-and-misconduct/))

**Alldredge and Cicero / Kang, Kim, Wang on cluster trading (2017–2018).** Cluster purchases (multiple insiders within a short window, typically ≤7 days) earn **~2.1% abnormal returns over the next month vs ~1.2% for solitary buys** (Alldredge-Cicero; cluster premium ≈ 0.9%/mo). Kang-Kim-Wang on 1986–2016 find cluster purchases earn 21-day CARs of **~3.8% vs 2.0%** for non-cluster, with the gap persisting to ~2.5% over 90 days. Cluster signals dominate solitary signals and are most informative when several different insiders (not just one repeat trader) participate. ([Wiley/JFR](https://onlinelibrary.wiley.com/doi/abs/10.1111/jfir.12172); [2iQ overview](https://www.2iqresearch.com/blog/what-is-cluster-buying-and-why-is-it-such-a-powerful-insider-signal))

**Recent ML / 10b5-1 work (2023–2025):**
- Zhao (2025, Stanford) "Insider Purchase Signals in Microcap Equities: Gradient Boosting Detection of Abnormal Returns" — 17,237 P-coded buys, $30M–$500M caps, 2018–2024; gradient-boosted classifier reaches AUC 0.70 OOS on 2024 data; distance-from-52-week-high explains 36% of feature importance; momentum (not mean reversion) dominates. ([arXiv 2602.06198](https://arxiv.org/pdf/2602.06198))
- "IFD: A Large-Scale Benchmark for Insider Filing Violation Detection" (2025) — 4,051,143 labeled Form 4 transactions; introduces Mamba+XGBoost hybrid for late-filing detection; useful for thinking about scale of EDGAR Form 4 corpus. ([arXiv 2507.20162](https://arxiv.org/html/2507.20162v1))

### 1(c) Critical / Negative Results

**Brochet (2010), "Information Content of Insider Trades Before and After the Sarbanes-Oxley Act," Accounting Review 85(2): 419–446.** Critical reference for SOX §403's two-business-day rule (effective Aug 2002). Pre-SOX, Form 4s had to be filed within 10 days after the *end of the calendar month* of the transaction. Post-SOX, abnormal returns and trading volumes around purchase filings became **significantly larger** (more informative because timelier), but for sales the abnormal-return effect is more muted on average — only after controlling for pre-planned trades, reporting lag, and litigation risk does a clear post-SOX negative association appear, consistent with regulators' deterrence reducing pre-bad-news selling. ([HBS](https://www.hbs.edu/faculty/Pages/item.aspx?num=36909); [AAA](https://publications.aaahq.org/accounting-review/article-abstract/85/2/419/3237/); [SSRN 1108731](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=1108731))

**Jagolinzer (2009), "SEC Rule 10b5-1 and Insiders' Strategic Trade," Management Science 55(2): 224–239.** Demonstrates that despite 10b5-1's intended safe-harbor structure, plan participants' sales **systematically follow positive firm performance and precede negative performance**, generating abnormal forward-looking returns larger than non-participating colleagues. Earlier (~Dec 2006 work referenced in subsequent commentary): plan trades outperformed market by ~6% over six months. The original empirical evidence motivating the WSJ 2012–2013 Pulliam/Barry exposés and the eventual 2022 amendment. ([INFORMS](https://pubsonline.informs.org/doi/10.1287/mnsc.1080.0928); [SSRN 541502](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=541502))

**Signal-decay evidence:** A 2025 Aalto thesis replication of Cohen-Malloy-Pomorski on 2008–2024 data finds opportunistic-buy alphas have **declined ~60–70%**, from ~1.2–1.6%/month in CMP's 1989–2007 sample to ~0.3–0.4%/month, and the long-short opportunistic-vs-routine spread has shrunk from ~0.7%/month (t≈3) to small and noisy. Sell-side alphas in particular are now weak and statistically insignificant. The qualitative ranking (opportunistic > routine) holds, but magnitudes are much smaller. ([Aalto thesis](https://aaltodoc.aalto.fi/server/api/core/bitstreams/fbbd1ec6-d5b4-44dd-881d-144ffd0ea21c/content)) Biggerstaff-Cicero-Wintoki ("Insider Trading Patterns") similarly find that even classified-routine traders show informed behavior once trade sequences are accounted for, complicating the clean CMP partition. ([Wichita](https://www.wichita.edu/academics/business/accountancy/documents/InsiderTradingPatternsWintokiNov2016.pdf); [ScienceDirect](https://www.sciencedirect.com/science/article/abs/pii/S0929119920300985))

**Reg-FD / decimalization context.** Brown & Hillegeist-style work shows Reg FD (Oct 2000) reduced informed-trading proxies, but **decimalization (2001) had a much larger impact** on Hasbrouck informativeness statistics — meaning attribution of signal decay to any single rule change is fragile. ([ScienceDirect Reg-FD paper](https://www.sciencedirect.com/science/article/abs/pii/S0929119906000393))

**Net assessment for Layer 2:** the buy signal remains directionally robust but smaller in magnitude than the headline 1989–2007 numbers; the sell signal has materially weakened as a standalone; and the right benchmark is now opportunistic-only with regime breaks at SOX (Aug 2002), Reg FD (Oct 2000), EDGAR same-day-filing operational reality (~2003+), and the 10b5-1 reform (Feb 27, 2023).

---

## 2. Quant-Finance Grounding — How Insider Trading Actually Works

### 2(a) Form 4 Mechanics
- **Who must file:** under Section 16(a) of the Securities Exchange Act of 1934, "insiders" = (i) directors, (ii) designated/Section 16 officers (CEO, CFO, COO, principal accounting officer, and others with policy-making authority and access to MNPI), and (iii) any beneficial owner of >10% of a registered class of equity securities. ([SEC](https://www.sec.gov/resources-small-businesses/going-public/officers-directors-10-shareholders); [Cornell CFR 17 §240.16a-2](https://www.law.cornell.edu/cfr/text/17/240.16a-2); [Paul Hastings](https://www.paulhastings.com/insights/client-alerts/sec-reporting-obligations-under-section-13-and-section-16-of-the-exchange))
- **Filing timeline:** SOX §403 (effective Aug 29, 2002) requires Form 4 within **two business days of the transaction**. Pre-SOX rule was within 10 days after the close of the calendar month. ([Brochet 2010](https://corpgov.law.harvard.edu/2009/10/30/sox-and-insider-trades/))
- **Forms 3, 4, 5 relationship:**
  - **Form 3**: initial statement of beneficial ownership at the time the person becomes a Section 16 reporter (within 10 days).
  - **Form 4**: routine ongoing disclosure of changes in beneficial ownership (T+2 business days).
  - **Form 5**: annual catch-up form for exempt or previously-unreported transactions; due 45 days after fiscal year end. ([SEC Investor Bulletin "Insider Transactions and Forms 3, 4, and 5"](https://www.sec.gov/files/forms-3-4-5.pdf))
- **Direct vs indirect ownership:** "direct" = held in the insider's own name; "indirect" = held by a related entity in which the insider has a pecuniary interest (family trust, LP, spouse, etc.). The pecuniary-interest test determines reportability. Indirect transactions matter — a non-trivial share of large founder/director activity flows through trusts and LPs.
- **Derivative vs non-derivative tables:** Form 4 has Table I (non-derivative — common stock) and Table II (derivative — options, warrants, RSUs, convertibles). Conversions/exercises (M, X) move shares from Table II to Table I. A common parsing pitfall is double-counting an exercise + sale combo.

**Transaction codes (SEC official; [SEC ownership form codes](https://www.sec.gov/edgar/searchedgar/ownershipformcodes.html); [SEC Investor Bulletin](https://www.sec.gov/files/forms-3-4-5.pdf)):**
- `P` — open-market or private **purchase** (highest signal value)
- `S` — open-market or private **sale**
- `A` — grant/award/acquisition under Rule 16b-3 (compensation, low signal)
- `D` — disposition back to issuer under 16b-3 (often exercise-and-immediate-sell back)
- `F` — payment of exercise price or tax via shares withheld (mechanical, **not a discretionary sale** — should be filtered out)
- `M` — exercise/conversion of derivative under 16b-3
- `X` — exercise of in/at-the-money option (non-16b-3)
- `C` — conversion of derivative
- `G` — gift (not a directional signal but can mask wealth transfer/tax planning)
- `K` — equity swap or hedging transaction (signal of bearish hedging by insider)
- `V` — voluntarily reported transaction (often used to flag 10b5-1 plan trades; post-2023 there is a separate Form 4 checkbox for 10b5-1 plan trades)
- `J` — other (footnoted)
- `I` — discretionary transaction under 16b-3(f)
- `E`, `H`, `O` — derivative expirations/cancellations
- `Z` — voluntary holding via deferred-comp plan

For a pure "do" signal, the canonical baseline is `P − S` aggregated by insider/quarter/firm, with `F`, `A`, `D` excluded (mechanical), `M+X→S` chains carefully decomposed, and `V`-flagged or 10b5-1-flagged trades segregated.

### 2(b) Open vs Closed Window Periods
Most public companies impose **quarterly blackout windows** typically beginning 2–4 weeks before quarter-end (varying by company; a 2024–2025 Wilson Sonsini SV150 survey found 23% close >25 days before quarter-end) and ending **1–2 full trading days after the earnings release**. A common Section-16-officer policy ends blackout the second trading day after the earnings press release; ~46% of companies require a 2-day post-release wait, ~29% require 1 day. ([Orrick](https://www.orrick.com/en/Insights/2024/06/Insider-Trading-Policy-Key-Terms-and-Trends); [Perkins Coie](https://perkinscoie.com/public-company-handbook-chapter-6-insider-reporting-obligations-and-insider-trading-restrictions); [NASPP](https://www.naspp.com/blog/4-Trends-in-Trading-Blackout-Periods); [Wilson Sonsini SV150 survey](https://www.wsgr.com/a/web/bPTkLm9NChAxLS7DiWkjfv/wilsonsonsini_insider_trading_report_20251111.pdf))

**Key signal-relevance fact:** trades inside the **open window** (post-earnings-release through the next quarter cut-off) are exactly the periods when the asymmetric-info concern is at its lowest by company policy — but these are also the only times non-plan discretionary trades can occur. Therefore **most discretionary opportunistic-trade signal lives in the open-window**, not the blackout. Trades during blackout are almost always 10b5-1 plan trades or pre-cleared exceptions. The MNPI doctrine under Rule 10b-5 is independent of blackout policy: even an open-window trade is illegal if the insider has MNPI.

### 2(c) 10b5-1 Plans
- **What they are:** Rule 10b5-1(c)(1) (adopted 2000) provides an affirmative defense against insider-trading liability for trades made under a written plan or formula adopted when the insider was *not* aware of MNPI, and over which the insider has no subsequent influence. ([SEC final rule release; Skadden alert](https://www.skadden.com/insights/publications/2022/12/sec-amends-rules-for-rule-10b51-trading-plans-and-adds-new-disclosure-requirement))
- **Pre-Dec-2022 abuses:** no mandatory cooling-off period, easy mid-stream modification, multiple overlapping plans, single-trade plans, no public disclosure of plan adoption, ability to cancel ahead of bad news (insider abstention). Larcker et al. (2021) found ~31% of plan trades occurred within 90 days of adoption pre-amendment. WSJ (2012–2013, Pulliam/Barry) provided the foundational journalism. Estimated ~50% of S&P 500 companies had executives using 10b5-1 plans by 2019. ([Harvard Corp Gov, Larcker Stanford working paper](https://corpgov.law.harvard.edu/2021/01/28/gaming-the-system-three-red-flags-of-potential-10b5-1-abuse/))
- **Dec 14, 2022 SEC amendments (effective Feb 27, 2023; Form 4/5 amendments effective Apr 1, 2023):** ([SEC press release 2022-222](https://www.sec.gov/newsroom/press-releases/2022-222); [Morgan Lewis](https://www.morganlewis.com/pubs/2022/12/sec-adopts-significant-changes-to-rule-10b5-1-affecting-trading-by-insiders); [Skadden](https://www.skadden.com/insights/publications/2022/12/sec-amends-rules-for-rule-10b51-trading-plans-and-adds-new-disclosure-requirement); [Cadwalader/CLS Blue Sky](https://clsbluesky.law.columbia.edu/2023/01/25/cadwalader-discusses-new-sec-rule-10b5-1-trading-plan-rules/))
  - **Cooling-off period** for directors/officers: later of (i) 90 days after adoption/modification, or (ii) two business days after the issuer's filing of 10-Q/10-K covering the fiscal quarter of adoption — capped at 120 days.
  - **30-day cooling-off** for non-issuer non-D&O persons; **no cooling-off for issuers themselves** (e.g., share-repurchase plans).
  - **Director/officer good-faith certification** at adoption: not aware of MNPI; adopting in good faith.
  - **Prohibition on overlapping plans** (with limited exceptions for sell-to-cover-tax and successive plans).
  - **Single-trade plans limited** to one per 12-month period (per non-issuer person).
  - **Form 4/5 mandatory checkbox** identifying 10b5-1 plan trades (effective Apr 1, 2023).
  - **Quarterly issuer disclosure** (10-Q/10-K) of plan adoptions/modifications/terminations by D&Os, with material terms (excluding pricing).
  - **Annual disclosure** of insider-trading policies; new disclosure of option-grant timing near MNPI events; **gifts now report on Form 4 within T+2** instead of via Form 5.
- **Cohen-Jackson-Malloy-Nguyen line:** the user's referenced "say-do gap"-adjacent line of work — Jagolinzer (2009) and the Cohen-Jackson-Malloy-Nguyen extensions documented systematic outperformance of 10b5-1 trades vs non-plan trades pre-reform. Larcker et al. (2021) provided the comprehensive 20K-plan empirical follow-up. Kim-Kim-Rajgopal (2025) provides post-reform evidence the reform worked: trades within 90 days of adoption fell from 31.1% to 1.7%, and post-amendment plan trades produce flat/slightly positive subsequent abnormal returns instead of the prior negative pattern. ([SSRN 5362431](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=5362431))

**Layer 2 implication:** treat pre- and post-Feb-2023 data as separate regimes. Pre-2023, a 10b5-1-flagged sale should still be treated cautiously as potentially informed; post-2023, plan-flagged sales are largely cleansed of opportunism but retain residual liquidity/diversification noise.

### 2(d) Buy vs Sell Asymmetry
Lakonishok-Lee (2001) and Jeng-Metrick-Zeckhauser (2003) both establish that **purchases drive nearly all the predictive power**; sales are noisier because insiders sell for diversification, taxes, divorce, college tuition, founder cash-out, charitable giving, estate planning. Insiders are already long their company through compensation — every additional purchase is an out-of-pocket overweight bet. Peter Lynch's aphorism captures the intuition: insiders sell for many reasons, but they buy for only one. Modern post-decimalization data (Jeng-Metrick numbers above; Aalto 2025 replication) suggests sell-side alpha has nearly vanished as a standalone, while buy-side alpha has compressed but persists. CFO-purchase signals slightly outperform CEO-purchase signals on average (Wang-Shin-Francis "Why are CFO Insider Trades More Informative" — scrutiny hypothesis: CEOs face more visibility and self-throttle).

### 2(e) Cluster Buying & Routine vs Opportunistic
- **Cohen-Malloy-Pomorski (2012) classification:** for each insider with at least 3 consecutive years of trading history, classify as routine if they have a trade in the same calendar month every one of those years; else opportunistic. Apply forward — all post-classification trades take the inherited label. Routine trades have alphas indistinguishable from zero; opportunistic trades carry essentially all the predictive power. ([NBER w16454 PDF](https://www.nber.org/system/files/working_papers/w16454/w16454.pdf))
- **Cluster definition:** Alldredge-Cicero use a 2-day peer-trade window; Kang-Kim-Wang use ≤7 days; commercial vendors typically use 7-day windows of distinct insiders trading the same direction. Cluster purchases ≈ 2× the 21-day CAR of solitary purchases per Kang-Kim-Wang (3.8% vs 2.0%). Cluster + opportunistic + executive-tier is the gold-standard "high conviction" filter.
- **Role weighting:** the empirical literature consistently ranks signal value as roughly **CEO ≈ CFO > other Section 16 officers > board members > 10% beneficial owners > others**. CFO trades are slightly more profitable in some samples than CEO trades, attributed to CEOs' higher visibility and self-throttling. ([ResearchGate "Why are CFO Insider Trades More Informative"](https://www.researchgate.net/publication/228248991_Why_are_CFO_Insider_Trades_More_Informative))

### 2(f) The Say-Do Gap Concept
This is Layer 2's distinctive angle. Existing literature touches the concept but does not, to my knowledge, formalize it as a unified divergence score:

- **Rogers, Van Buskirk, Zechman (2011), "Disclosure Tone and Shareholder Litigation," The Accounting Review 86(6): 2155–2183.** Most directly on point. Using both general-purpose and Loughran-McDonald-style finance dictionaries, they show plaintiffs preferentially sue firms whose earnings announcements were unusually optimistic and **whose insiders were abnormally selling at the same time**. Litigation risk is materially higher when optimistic tone and abnormal insider sales co-occur. This is the closest formal precedent for the say-do divergence signal; they demonstrate it has real economic content via the litigation channel, but they do not build it into a forward-return predictor or productize it. ([SSRN 1331608](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=1331608))
- **Cheng & Lo (2006), "Insider Trading and Voluntary Disclosures," J. Accounting Research 44(5).** When managers plan to purchase shares, they increase bad-news forecasts to depress purchase price; trade timing around bad-news guidance shows accumulation post-disclosure. Direct evidence that disclosure and trading are jointly strategic. ([RePEc/JAR](https://ideas.repec.org/a/eee/jaecon/v55y2013i1p43-65.html))
- **Brochet/NYU (2017) on Indian markets and Brochet-Naranjo-Yu**: insiders curtail trading right before negative earnings news; insider purchases preempt earnings news; the sign-and-magnitude relationship between disclosure and trading is information-driven.
- **Hoberg-Lewis (2017), "Do Fraudulent Firms Produce Abnormal Disclosure?"** Uses cosine-similarity attribute models on 10-K MD&A text; fraudulent firms' verbal disclosure is abnormal vs strong counterfactuals. Methodologically relevant to representing the "say" side as a vector and comparing trajectories. ([SSRN 2298302](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=2298302))
- **Jagolinzer (2009)** documents, in the 10b5-1 context, that the very existence of the affirmative defense incentivizes executives to **keep saying optimistic things** while the plan executes scheduled sales — i.e., the say-do gap may be amplified, not reduced, by the safe harbor (per Cohen Milstein commentary, [Cohen Milstein](https://www.cohenmilstein.com/update/%E2%80%9Cit%E2%80%99s-time-rescind-get-out-jail-free-card-afforded-executives-10b5-1-plans%E2%80%9D-new-york-law)).
- **Insider Abstention (Fried; UChicago Business Law Review).** A subtle but important piece: a substantial amount of "insider-trading information" is encoded in *not trading* — when an executive who normally diversifies stops doing so, it can be informative. Recent enforcement (Peizer/Ontrak Mar 2023; Cheetah Mobile Sep 2022) has explicitly targeted plan-cancellation-as-MNPI-trading. ([UChicago BLR](https://businesslawreview.uchicago.edu/print-archive/insider-abstention-and-rule-10b5-1-plans))

**Net assessment:** the formal "say-do gap" as a unified quantitative score with both directions (positive talk + selling, and negative talk + buying) is genuinely a research gap. Rogers/Van Buskirk/Zechman is the closest precedent and is one-directional (litigation risk on optimism+sales). Layer 2's contribution is therefore both methodological (a symmetric divergence score) and integrative (combining the existing language and Form-4 literatures into one forward-looking signal).

---

## 3. Data Source Investigation

### 3(a) SEC EDGAR (canonical, free)
- **Access:**
  - Full-text search API: `https://efts.sec.gov/LATEST/search-index?q=...&forms=4`
  - Submissions API: `https://data.sec.gov/submissions/CIK{cik}.json`
  - Direct file downloads: filings under `https://www.sec.gov/Archives/edgar/data/{cik}/{accession_no_dashes_removed}/`
  - Daily/quarterly indexes at `https://www.sec.gov/Archives/edgar/full-index/`
- **Form 4 file format:** XML conforming to the **EDGAR Ownership XML Technical Specification** (`ownershipDocument.xsd`). Each Form 4 contains a `reportingOwner` block, an `issuer` block, optional `nonDerivativeTable` (Table I) and `derivativeTable` (Table II), each with `nonDerivativeTransaction`/`derivativeTransaction` children carrying `transactionDate`, `transactionCoding/transactionCode`, `transactionAmounts/transactionShares`, `transactionPricePerShare`, `postTransactionAmounts/sharesOwnedFollowingTransaction`, and a `nature OfOwnership` (D = direct, I = indirect). ([SEC EDGAR Ownership XML Tech Spec v5.1](https://www.sec.gov/info/edgar/ownershipxmltechspec-v3.pdf); [example Form 4 XML](https://www.sec.gov/Archives/edgar/data/1067983/000095017024114125/xslF345X05/ownership.xml))
- **URL structure:** `https://www.sec.gov/Archives/edgar/data/{cik}/{accession-no-dashes-removed}/{primary_doc}.xml`
- **Rate limit:** 10 requests/second per IP (announced July 2021); user-agent header is mandatory. Exceeding the cap returns 403 and triggers a ~10-minute IP cooldown. Best practice: throttle to 8–9 req/s, set `User-Agent: "ProjectName email@example.com"`, exponential-backoff on 429/403, cache aggressively. ([SEC](https://www.sec.gov/filergroup/announcements-old/new-rate-control-limits); [tldrfiling](https://tldrfiling.com/blog/sec-edgar-api-rate-limits-best-practices))
- **Cost:** free.
- **Coverage:** electronic filings on EDGAR from 1993; mandatory electronic Form 4 filing (and same-day Internet posting requirement) effective **June 30, 2003** under SOX §403/Reg S-T. Pre-2003 paper Form 4s were re-keyed by data vendors and have material data quality issues.
- **Data quality issues:**
  - Amended filings (Form 4/A): non-trivial fraction; you must reconcile amendments back to original transactions.
  - Late filings: SOX §403's two-day rule is widely complied with but late filings are commonly disclosed in proxy "Section 16(a) compliance" sections; persistent late-filer behavior itself can be a signal (cf. IFD 2025 paper).
  - Footnote-only modifications (transaction code `J`, gift `G`, voluntary `V`) require parsing the free-text footnotes to interpret correctly.
  - Manual transcription errors in pre-2003 data — pre-electronic filings were keyed by SEC contractors with documented error rates.
  - Same-insider-multiple-CIK joining: an executive at multiple firms gets multiple reporting-owner CIKs; canonical insider IDs must be reconstructed.

### 3(b) Python Libraries

- **`sec-edgar-downloader` (jadchaar):** simplest wrapper; downloads raw filings to disk by ticker/CIK/form type. Doesn't parse XML — you handle that yourself. ([readthedocs](https://sec-edgar-downloader.readthedocs.io/))
- **`edgartools` (dgunning, Anthropic Open Source program member as of 2025):** the most production-grade modern choice. Handles rate limiting, identity headers, and parses Form 4 directly into typed Python objects with `.transactions` DataFrames. Includes automatic backoff, lxml/PyArrow performance, MCP server support for AI workflows. Supports 17+ form types. Free, MIT-licensed. ([GitHub](https://github.com/dgunning/edgartools); [PyPI](https://pypi.org/project/edgartools/); [readthedocs complete guide](https://edgartools.readthedocs.io/en/stable/complete-guide/))
- **`python-edgar` / `py-edgar` (joeyism):** thin wrapper around EDGAR full-text search and indexes. Older; rate-limit awareness was retrofitted via a community PR. Less complete than edgartools.
- **`py-sec-edgar` (ryansmccoy):** workflow-oriented downloader, supports daily/RSS workflows. ([GitHub](https://github.com/ryansmccoy/py-sec-edgar))
- **`finagg`:** newer, primarily focused on aggregating SEC + FRED + Yahoo into a unified DB; less specialized for Form-4 parsing than edgartools.
- **`sec-api.io`:** commercial hosted REST API; 40 req/s rate, JSON-only. Useful when you want pre-parsed Form 4 JSON without running EDGAR scrapers; tiered pricing typically starts ~$50–$500/month for individual quant use.
- **Recommendation:** for the Narrative Atlas philosophy of immutable raw data, `edgartools` (or `sec-edgar-downloader` for raw + a thin XML parser) is the right choice — it preserves source provenance, is free, has deterministic behavior, and won't introduce paid-vendor lock-in. Treat openinsider as a sanity-check oracle, not the source of truth.

### 3(c) Commercial Data Providers
- **The Washington Service (WS, founded 1970, now part of LSEG/Refinitiv ecosystem):** the institutional standard. Provides Form 3/4/5 and Form 144 data with hand-cleaned normalization (name disambiguation, related-entity linking, transaction-code corrections). Multiple feed tiers: Basic Insider Feed (Form 4/5 from Oct 2003), Form 144 from Feb 2005, Quant feed (Jan 2006+) with revision history and timestamps for cleaned-vs-raw comparison. Bloomberg, Dow Jones, Refinitiv all source insider news from WS. Has a separate proprietary 10b5-1 plan database covering disclosed plans from 2016. Not publicly priced — institutional contracts typically run $20K–$100K+/year for low-latency feeds; API access is more modest. ([Washington Service](https://www.washingtonservice.com/all-products/us-insider-trading/); [LSEG product page](https://www.lseg.com/en/data-analytics/financial-data/news/washington-service))
- **Bloomberg `INSD <GO>`:** standard terminal function; sourced from WS for news feeds.
- **WhaleWisdom / InsiderScore (now Verity):** institutional research-oriented insider analytics. Verity acquired InsiderScore; pricing typically $5K–$30K/year.
- **2iQ Research:** Frankfurt-based, comprehensive global coverage including non-US insider data; institutional clients.
- **OpenInsider (free, http://openinsider.com):** scraped from EDGAR; the most popular free aggregator in the retail/quant-research community. Data from 2003+; JSON/CSV not officially exposed but multiple community scrapers exist (e.g., sd3v/openinsiderData on GitHub). Signal-quality is fine for backtesting but doesn't include hand-cleaning. Good as a cross-check oracle. ([OpenInsider](http://openinsider.com/))
- **Other free aggregators:** Fintel, GuruFocus, InsiderMonkey, Barchart — all derivative of EDGAR.

### 3(d) Representative Form 4 XML
A typical Form 4 ownershipDocument has this structure (paraphrased from EDGAR XML Tech Spec; concrete example: [Berkshire/Apple Form 4](https://www.sec.gov/Archives/edgar/data/1067983/000095017024114125/xslF345X05/ownership.xml)):

```
<ownershipDocument>
  <schemaVersion>X0508</schemaVersion>
  <documentType>4</documentType>
  <periodOfReport>2024-MM-DD</periodOfReport>
  <issuer>
    <issuerCik>0000320193</issuerCik>
    <issuerName>Apple Inc.</issuerName>
    <issuerTradingSymbol>AAPL</issuerTradingSymbol>
  </issuer>
  <reportingOwner>
    <reportingOwnerId>
      <rptOwnerCik>0001214156</rptOwnerCik>
      <rptOwnerName>COOK TIMOTHY D</rptOwnerName>
    </reportingOwnerId>
    <reportingOwnerRelationship>
      <isDirector>0</isDirector>
      <isOfficer>1</isOfficer>
      <officerTitle>Chief Executive Officer</officerTitle>
    </reportingOwnerRelationship>
  </reportingOwner>
  <nonDerivativeTable>
    <nonDerivativeTransaction>
      <securityTitle><value>Common Stock</value></securityTitle>
      <transactionDate><value>2024-MM-DD</value></transactionDate>
      <transactionCoding>
        <transactionFormType>4</transactionFormType>
        <transactionCode>S</transactionCode>
        <equitySwapInvolved>0</equitySwapInvolved>
      </transactionCoding>
      <transactionAmounts>
        <transactionShares><value>50000</value></transactionShares>
        <transactionPricePerShare><value>175.42</value></transactionPricePerShare>
        <transactionAcquiredDisposedCode><value>D</value></transactionAcquiredDisposedCode>
      </transactionAmounts>
      <postTransactionAmounts>
        <sharesOwnedFollowingTransaction><value>3265000</value></sharesOwnedFollowingTransaction>
      </postTransactionAmounts>
      <ownershipNature>
        <directOrIndirectOwnership><value>D</value></directOrIndirectOwnership>
      </ownershipNature>
    </nonDerivativeTransaction>
  </nonDerivativeTable>
  <derivativeTable>...</derivativeTable>
  <footnotes>...</footnotes>
  <ownerSignature>...</ownerSignature>
</ownershipDocument>
```

**Common parsing gotchas:**
- A single Form 4 can contain multiple transactions on different dates (one filing for a batch of plan trades).
- M+S pairs (option exercise + immediate sale): the M leg shows on the derivative table with code `M` and acquisitionDispositionCode `A`; the S leg shows on the non-derivative table — easy to double-count if you sum naively.
- F transactions ("payment of exercise price or tax liability"): often appear next to S/M and look like sales, but they're share-withholding mechanics, not discretionary sales — must be filtered out before computing net dollar volume.
- Gifts (`G`): a non-zero share count with $0 price; can mask wealth transfers, charitable giving, or family planning. Post-Apr 2023 these must report on Form 4 (T+2) rather than Form 5 — adds noise to recent data vs older.
- 10b5-1 V-flag (pre-2023): inconsistent usage. Post-Apr 2023, a separate dedicated checkbox identifies 10b5-1 plan trades — much cleaner.
- Indirect ownership through nested entities: you must reconcile pecuniary-interest claims via footnotes.
- Stock splits, mergers, reorganizations: insiders sometimes file Form 4s for accounting reasons even though no economic change occurred — these often appear with code `J` plus a footnote.

### 3(e) Corpus Size
- The SEC publishes a quarterly file `sec.gov/data-research/sec-markets-data/number-edgar-filings-form-type` listing counts by form type per year. Per a sec-api.io analysis of SEC's data, **Form 4 represented ~29% of all EDGAR filings in 2022**, the single largest filing category by volume. ([sec-api.io trends analysis](https://sec-api.io/resources/analyzing-sec-edgar-filing-trends-and-patterns-from-1994-to-2022))
- The IFD benchmark paper assembled **~4.05 million labeled Form 4 transactions** spanning multi-year coverage ([arXiv 2507.20162](https://arxiv.org/html/2507.20162v1)), implying annual Form-4 filing volume in the **roughly 300K–500K filings/year** range (each filing carries 1–N transactions; total transaction counts run higher).
- Storage: a typical Form 4 XML is 5–20 KB. Full historical corpus 1994–present at ~400K filings/year ≈ **40–60 GB of raw XML uncompressed**, easily compressible by ~10× with zstd/gzip. After parsing into a normalized parquet/SQLite store keyed by (cik, accession, transaction_id), the working dataset is well under 5 GB — trivial for a 4090 box.

---

## 4. NLP/ML Technique for the Say-Do Gap

### 4(a) The "Say" side (Layer 4 output, already implemented)
Layer 4 produces per-headline FinBERT/LogReg/VADER sentiment scores using `ProsusAI/finbert` plus VADER and a logistic baseline. To feed Layer 2, this needs to be aggregated to **per-executive (or per-firm), per-time-window** sentiment trajectories:

1. **Filter the corpus** to documents attributable to a specific executive: earnings call transcripts (segregating prepared remarks vs Q&A by speaker labels — common in CapIQ, Refinitiv Eikon transcripts, or AlphaSense), press-release quotes, 8-K text where signed, conference appearances. Only first-person executive-attributed text is "say."
2. **Aggregate** per executive per quarter (or rolling 90-day window): mean FinBERT positive-minus-negative score, weighted by document length or prominence (earnings calls > press releases > conference Q&A).
3. **Z-score** within executive (relative to that exec's own historical baseline) to control for chronic optimists/pessimists.
4. Output: per (executive, period) say_score ∈ ℝ, where 0 ≈ baseline, +1 ≈ unusually optimistic, −1 ≈ unusually cautious.

### 4(b) The "Do" side
1. **Pull all Form 4s** for the executive + period from the immutable EDGAR raw store.
2. **Filter:** keep `P` and `S` transactions; drop `A`, `F`, `D`, `M` (alone), `G`, `J` unless analyzing tax/founder behavior. Decompose `M+S` chains.
3. **Apply Cohen-Malloy-Pomorski opportunistic filter:** classify each insider's history; for executives with ≥3y of trading history, flag routine vs opportunistic by same-calendar-month rule. For executives with insufficient history, treat as opportunistic by default (conservative).
4. **Apply Ali-Hirshleifer past-profitability filter** (optional second-layer): rank insiders by historical pre-QEA trading profitability; high-rank insiders have stronger forward signals.
5. **Net dollar value:** `do_dollar = sum(P transactions × price) − sum(S transactions × price)`, scaled by the executive's prior-period normal trading dollar volume (or by the firm's median market cap).
6. **Role weighting:** multiply by role weight — empirically calibrated as roughly CEO 1.0, CFO 1.0, COO 0.7, other Section 16 officers 0.5, board members 0.4, 10% beneficial owners 0.3 (founder-blockholders 0.1 — see failure modes). Cluster bonus: if ≥2 distinct insiders trade same direction within 7 days, multiply by 1.5×.
7. **Z-score** within executive across history.
8. Output: per (executive, period) do_score ∈ ℝ, with sign = direction (+ buying, − selling) and magnitude = standardized intensity.

### 4(c) Combining — Alignment vs Divergence Score
The four-cell taxonomy:

| Say | Do | Interpretation | Layer 2 Score |
|-----|----|----|---|
| + | + | Aligned bull | low \|divergence\| |
| + | − | **DIVERGENCE — bearish** (insiders don't believe their own talk; selling into optimism — the Enron / Rogers-Van Buskirk-Zechman pattern) | high +divergence |
| − | + | **DIVERGENCE — bullish** (managing expectations while accumulating — Buffett-on-buybacks / contrarian-CEO pattern) | high −divergence |
| − | − | Aligned bear | low \|divergence\| |

**Concrete construction options:**
- **Signed difference (simplest):** `divergence = say_score − do_score` after both are z-normalized. Positive = saying more bullish than doing; negative = saying more bearish than doing. The sign aligns with bearish/bullish forward expectation under the say-do thesis.
- **Vector decomposition:** treat (say, do) as 2D points. The aligned axis is y=x; the divergence axis is y=−x. Project onto y=−x: `divergence = (say − do)/√2`. Equivalent to signed difference but normalized.
- **Cosine similarity over trajectories:** for a window of past T quarters, compute the cosine similarity between the `say_score[t-T:t]` time series and `do_score[t-T:t]`. Cosine ≈ 1 means aligned, ≈ −1 means systematically divergent. More robust to single-quarter outliers but laggier.
- **Granger causality:** test whether `do_score[t]` Granger-causes `say_score[t+k]` (or vice versa) at the firm or sector level. Useful for OPEN QUESTION (a) — does saying lead doing or doing lead saying?
- **Event-study for divergence events:** define a "divergence event" as |divergence| > 2σ over rolling baseline; estimate forward CAR over (0, +21) and (0, +63) day windows controlling for size, BM, momentum (Carhart 4-factor); compare to non-event firms.

### 4(d) Compute Requirements
- Layer 4 sentiment is already running on FinBERT/LogReg/VADER — likely the dominant cost; a single FinBERT pass over ~500K-document corpus on a 4090 with batch size 64 is ~hours, not days.
- Form 4 parsing: trivial. ~500K files/year × 20 KB → 10 GB; lxml parsing at >5K filings/sec on a 4090 box; full historical reparse in tens of minutes.
- Aggregation, z-scoring, and divergence computation: pandas-trivial.
- Backtest portfolio construction: vectorized numpy/pandas; minutes, not hours.
- The whole layer comfortably fits in the existing `BaseScorer` ABC — the scorer is stateless per (executive, period) given Layer 4 outputs and Form 4 raw data.

---

## 5. Validation Strategy

### 5(a) Known-Pattern Backtests
- **Enron 2001** (the canonical case): 29 executives and directors sold $1.1 billion in Enron stock from 1999 to mid-2001 while issuing repeatedly bullish public statements; Skilling alone grossed ~$63M and made an alleged $15.5M Sept 17, 2001 trade after material non-public information about hidden losses. Enron is the textbook positive (Say+, Do−) divergence case. ([Wikipedia/Enron scandal](https://en.wikipedia.org/wiki/Enron_scandal); [Wikipedia/Enron](https://en.wikipedia.org/wiki/Enron); [NBC News](https://www.nbcnews.com/id/wbna12037553); [Natural Gas Intel](https://naturalgasintel.com/news/lay-confronted-about-2001-stock-sales-sons-short-selling/)). Insider-trading-before-accounting-scandals empirical work (ScienceDirect S0929119915000784) generalizes the pattern across Adelphia, Best Buy, JDS Uniphase, K-Mart, Lucent, Rite-Aid, Worldcom, Xerox, HealthSouth, Qwest. **Layer 2 should recover Enron 2001 as a 3σ+ Say+/Do− divergence event well before Oct 2001.**
- **HealthSouth/Scrushy** (concurrent fraud): another Say+/Do− backtest, with Scrushy selling hundreds of millions while running massive accounting fraud.
- **Cheetah Mobile (Sep 2022 SEC enforcement) and Ontrak/Peizer (Mar 2023):** two recent SEC-prosecuted cases where 10b5-1 plan adoptions co-occurred with optimistic public messaging and pending bad news. Smaller-scale post-reform validation cases. ([UChicago BLR](https://businesslawreview.uchicago.edu/print-archive/insider-abstention-and-rule-10b5-1-plans))
- **2022–2023 tech layoff cycle:** Meta, Salesforce, etc., where executives publicly defended growth strategy while Form 4 sells continued under 10b5-1 plans. Mixed cases — some had legitimate diversification needs (Zuckerberg/Bezos), others arguably opportunistic. Use as ambiguity benchmark.
- **Buffett–Apple accumulation 2016–2018:** Berkshire Hathaway's positive-public-tone-plus-buying as the canonical Say+/Do+ aligned-bull baseline (low divergence).
- **Bezos 10b5-1 sales 2024–2025:** $13.5B in 2024 and ~$5.4B in 2025, all under 10b5-1 plans, alongside continued positive public commentary on Amazon/AWS/AI strategy. Stock outperformed. **Negative test case** — Layer 2 must not flag this as a Say+/Do− divergence; the role-weighting (founder-blockholder weight ≈ 0.1) plus 10b5-1-flag plus "diversification founder" failure-mode rule should down-weight it appropriately. ([Globe and Mail/Bezos](https://www.theglobeandmail.com/investing/markets/stocks/META/pressreleases/32199336/); [Crain Currency](https://www.craincurrency.com/investing/bezos-catz-dell-cashed-out-billions-top-insider-sellers-2025))
- **Zuckerberg/Meta 2025**: ~$945M sold via 10b5-1 with Meta stock up 13% YTD on AI optimism — same negative test case structure. ([Tradealgo](https://news.tradealgo.com/news/ahead-of-the-tariff-stock-route-zuckerberg-and-dimon-are-among-the-top-sellers/); [iTiger](https://www.itiger.com/news/1154487726))

### 5(b) CMP Opportunistic-vs-Routine as Filtering Validation
Replicate Cohen-Malloy-Pomorski (2012) on the Layer 2 corpus: opportunistic-only portfolios should show meaningfully larger forward abnormal returns than routine-only portfolios. If they don't, the filter is broken or the data is corrupted. The 2025 Aalto replication says expect ~0.3–0.4%/month spread in modern data, not the original 0.7–1.0%/month — set realistic targets.

### 5(c) Out-of-Sample Portfolio Backtests
- **Long-short:** monthly (or weekly) rebalanced portfolio, long bottom-decile divergence (Say− Do+), short top-decile (Say+ Do−). Evaluate vs Carhart 4-factor + Fama-French 5-factor; report alpha, t-stat, Sharpe, max drawdown, turnover, capacity.
- **Event study:** for divergence events |z| > 2, compute (0, +21d), (0, +63d), (0, +252d) CARs vs size/BM/momentum-matched controls. Expect Say+ Do− events to underperform; Say− Do+ events to outperform.
- **Walk-forward:** strict no-look-ahead — divergence at t uses only data available at t (Form 4s filed by t with their actual filing lags; Layer 4 sentiment from documents published by t).

### 5(d) Synthetic Tests
- Construct synthetic firms where you inject known divergence patterns (positive sentiment on synthetic transcripts + simulated Form 4 sells). Verify Layer 2 score recovers the planted signal at expected magnitude.
- Stability tests: bootstrap-resample the universe; confirm divergence-portfolio alpha remains positive across 80%+ of bootstrap draws (otherwise signal is fragile).

---

## 6. Failure Modes (be specific; defensible in interview)

(a) **10b5-1 plans pre-2023 contamination.** Pre-Feb-27-2023, a non-trivial fraction of "S" transactions are plan trades that look opportunistic but were technically pre-arranged. Larcker et al. show ~31% of plan trades happened within 90 days of plan adoption, with documented loss-avoidance patterns. **Mitigation:** segregate pre-2023 vs post-2023 data; for post-2023 use the new Form 4 10b5-1 checkbox to filter; for pre-2023 use the V-flag and Washington Service plan database (or commercial 10b5-1 disclosure databases) where available; treat plan-flagged trades as lower-weight but not zero.

(b) **Tax-motivated sells.** End-of-year (Nov–Dec) selling for capital-gains harvesting; sells immediately after vest dates (RSU vest → sell to cover or sell to diversify); sells on stock-option expiration deadlines. Creates false-divergence Say+/Do− patterns. **Mitigation:** flag transactions within ±5 days of: vest dates (often visible in Form 4 footnotes), option expirations, end of fiscal year; down-weight these. The CMP routine-trader filter catches many of these but not all.

(c) **Founder/concentrated-wealth diversification.** Bezos, Zuckerberg, Dell, Catz, Huang sell large quantities under 10b5-1 plans for legitimate diversification, philanthropy, estate planning. These show up as massive Say+/Do− divergence under naive treatment. **Mitigation:** role-weight founder/blockholder trades very low (~0.1×); flag "10%+ beneficial owner" transactions separately; when more than ~50% of an insider's net worth remains in firm equity, treat sales as primarily diversification noise.

(d) **Ownership-requirement constraints.** Some companies require directors/officers to hold N shares or M× annual salary in equity. This caps net selling; what looks like "no Do signal" is actually "Do=zero by force." **Mitigation:** check proxy DEF 14A for stock-ownership guidelines; for affected insiders, treat near-zero net trading as low-information rather than aligned-bear.

(e) **Small-cap and micro-cap noise.** Form 4 signal is empirically strongest in small firms (Seyhun 1986, Lakonishok-Lee 2001, CMP 2012; Zhao 2025 microcap gradient-boosting paper) but also noisier per trade. Per-firm sample sizes of insider trades are small; single-trade noise dominates. **Mitigation:** require minimum threshold (e.g., ≥3 trades per firm-quarter or ≥$50K dollar-volume) before computing divergence; report confidence intervals.

(f) **M&A and tender-offer periods.** During announced or pending M&A, insiders are subject to additional restrictions (Rule 14e-3, tender-offer windows). Trades during these windows are unusual and not directly comparable. **Mitigation:** flag firms with active 8-K M&A disclosures; suspend Layer 2 scoring for the duration of the deal window.

(g) **Stock splits, spinoffs, acquisitions creating apparent transactions.** Mergers can trigger automatic exchange transactions reported on Form 4 even though no economic change occurred. Spinoffs distribute new ticker shares which appear as "acquisitions." **Mitigation:** filter `J` codes with split/merger/spinoff footnotes; cross-reference 8-K event dates; ignore zero-price transactions.

(h) **Dual-class share structures.** Founder-controlled firms (Meta, Google/Alphabet, Snap, NYT) where founders hold supervoting Class B shares — sales of Class B can be economically large but voting-control-preserving. The signal interpretation differs from single-class firms. **Mitigation:** flag dual-class issuers; report Class A and Class B trades separately.

(i) **Coverage gap between language and trading.** Layer 4 sentiment covers public-company executives in earnings calls / press releases — typically the CEO, CFO, and a few segment heads. Form 4 covers all Section 16 reporting persons (often 10–25 per firm). Misalignment: a board member's Form 4 has no Layer 4 counterpart; the CEO's earnings-call sentiment has no isolated do-side without disambiguating their personal Form 4 from the broader insider population. **Mitigation:** compute divergence at two levels — per-CEO/per-CFO (where both sides exist) and per-firm-aggregate (using CEO/CFO sentiment vs all-insider trading). Document which version each report uses.

(j) **Plan termination / abstention-as-signal.** Post-Feb-2023, an insider who terminates a 10b5-1 plan ahead of bad news avoids the sell-and-then-bad-news pattern entirely. The signal is "did not sell when expected." Layer 2 will miss this unless it tracks expected-vs-actual trading volume. **Mitigation:** for known-plan executives, model expected sell volume from prior plan; flag deviations.

(k) **Sentiment-model failure modes propagate.** FinBERT was trained on a specific financial-news corpus; misclassifies hedging language ("we anticipate growth rates to decelerate," "ongoing margin optimization") as neutral or even positive. Optimistic language is systematically over-weighted. **Mitigation:** rely on within-executive z-scoring rather than absolute scores; cross-validate FinBERT against LogReg + VADER (already in Layer 4); flag low-agreement cases.

(l) **Foreign Private Issuers were exempt from Section 16 historically.** Recent legislation (HFIAA / NDAA) extended Section 16 reporting to FPI directors and officers; SEC adopted final rules effective 2026. So Form 4 coverage of FPIs is partial historically and becoming complete only post-2026. **Mitigation:** scope Layer 2 to US domestic issuers initially; expand to FPIs as data accumulates. ([White & Case](https://www.whitecase.com/insight-alert/directors-and-officers-fpis-will-be-subject-section-16-reporting-requirements); [Sidley](https://www.sidley.com/en/insights/newsupdates/2025/12/us-legislation-subjects-directors-and-officers-of-foreign-private-issuers-to-section-16a-reporting); [Harvard Corp Gov 2026](https://corpgov.law.harvard.edu/2026/03/29/sec-adopts-final-rule-requiring-section-16a-reporting-for-officers-and-directors-of-foreign-private-issuers/))

---

## 7. Open Research Questions

(a) **Optimal time window for measuring "saying" vs "doing."** Type: **build to learn.** Earnings calls are quarterly; Form 4s are continuous. Likely ~30–90 day windows around earnings work best, but should be empirically tuned with walk-forward CV. Granger-causality tests on the Layer 2 corpus can reveal whether saying typically leads doing (executives reveal info verbally first) or doing leads saying (trades happen first; later language adjusts).

(b) **Whose statements count.** Type: **configurable parameter.** Default: CEO + CFO only (highest signal-per-document). Configurable to broaden to all named-executive-officer (NEO) speakers. Avoid IR / non-executive spokespeople — their statements aren't personally consequential.

(c) **Weighting CEO vs CFO vs board.** Type: **partly empirical, partly configurable.** Literature consensus puts CEO ≈ CFO > other Section 16 > board > 10%-owners. Empirically estimate role weights from in-sample forward-return coefficients; set as defaults; expose for sensitivity analysis.

(d) **Post-2013 EDGAR same-day-filing impact on signal decay.** Type: **field-level open problem.** Brochet (2010) showed SOX same-day filing made buy-signal more informative at filing (because faster diffusion concentrates the move) but reduced subsequent abnormal-return drift (because outsiders trade against insiders sooner). Whether this fully explains the post-2007 alpha decay (vs. simple arbitrage) is debated. Layer 2's interpretation: signal is now front-loaded into the (0, +5d) window rather than the (0, +252d) window; the layer should explicitly evaluate at multiple horizons.

(e) **"Filtered" insider data services (vendor pre-cleaning).** Type: **field-level genuine open problem.** Vendors like 2iQ and Verity sell filtered datasets that have already excluded routine, plan, and small trades. Are these filters capturing CMP/Ali-Hirshleifer-style real signal, or are they over-pruning? Biggerstaff-Cicero-Wintoki (2020) argue that even "routine" trades carry information once trade sequences are accounted for. **Layer 2's posture:** start with raw EDGAR + own filters; treat vendor-filtered data as an alternative not a substitute; compare results.

(f) **Cross-firm contagion / peer-insider trading.** Type: **build to learn / publishable extension.** Alldredge-Cicero (2017) document within-firm cluster trading. Cohen-Frazzini-Malloy and others have shown information networks across firms. A natural Layer 2 extension: when insiders at multiple peer firms simultaneously diverge in the same direction, the signal is amplified. Possible Granger-causality / network-momentum decomposition along Hirshleifer-Ali shared-analyst-coverage lines. ([NBER w25201](https://www.nber.org/papers/w25201))

(g) **Aggregation level: single-firm vs sector-aggregate vs market-aggregate.** Type: **configurable + field-level open problem.** Seyhun (1992, 1998) shows aggregate insider activity predicts up to ~60% of one-year-ahead aggregate market returns. CMP (2012) operates at the firm level. Layer 2 should expose all three aggregations: per-firm divergence (primary signal), sector-aggregated divergence (sector rotation signal), market-aggregated divergence (regime/macro signal). The literature suggests these are distinct and complementary.

---

## 8. Additional Context Integration & Implementation Notes

- Stack constraints (RTX 4090, Python 3.12, sklearn/transformers/pandas) match Layer 4 — no new dependencies needed beyond `lxml` (likely already installed via transformers) and a Form 4 parser. **Recommendation:** use `edgartools` for raw download + parsing, written outputs to `data/raw/edgar/form4/{cik}/{accession}.xml` (immutable), and a parquet view at `data/processed/form4/transactions.parquet` (regenerable from raw).
- The `BaseScorer` ABC fits cleanly: a `Layer2DivergenceScorer(BaseScorer)` returns a DataFrame with columns `divergence_score`, `divergence_label` (e.g., `aligned_bull`, `aligned_bear`, `bearish_divergence`, `bullish_divergence`), plus diagnostic columns (`say_z`, `do_z`, `n_trades`, `n_sentiment_docs`, `cluster_flag`, `opportunistic_flag`, `plan_flag`, `role_weight_used`).
- **Determinism:** sentiment z-scoring uses fixed historical windows; CMP classification uses deterministic same-month rule; only stochastic component is FinBERT inference (already deterministic given fixed seeds in Layer 4).
- **Provenance:** every divergence score should carry pointers back to (a) the underlying Form 4 accession numbers, (b) the underlying Layer 4 document IDs, and (c) the regime tag (pre-2023 plan rules vs post-2023). Then any backtest result can be drilled all the way back to source XML and source transcripts.
- **Configuration over magic numbers:** all role weights, cluster windows, opportunistic-classification window, CMP same-month threshold, blackout-window heuristic, founder-blockholder threshold, and sentiment aggregation window should live in a single YAML config. Default values should match published literature (CMP 3-year; cluster 7-day; etc.) so the layer is reproducible against academic baselines.
- **Defensible-in-interview talking points** (the user's stated goal):
  - Buy signal alpha has compressed materially post-2007 (~60–70% per Aalto 2025 replication of CMP); the layer is not claiming the original 82 bps/month — it's claiming a real but smaller signal augmented by the say-do divergence overlay.
  - Pre/post-Feb-2023 regime break is structural and explicitly modeled; the layer is robust to the 10b5-1 reform.
  - The say-do gap is a genuine research extension (Rogers-Van Buskirk-Zechman 2011 is the closest precedent; one-directional litigation focus, not a forward-return predictor); Narrative Atlas's contribution is the symmetric, productized formulation.
  - Failure modes are enumerated and have explicit mitigations rather than being hand-waved.

---

## References (Primary)

- Jeng, Metrick, Zeckhauser (2003). [SSRN](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=146029) | [MIT Press](https://direct.mit.edu/rest/article-abstract/85/2/453/57400/)
- Cohen, Malloy, Pomorski (2012). [NBER w16454](https://www.nber.org/papers/w16454) | [JOF](https://onlinelibrary.wiley.com/doi/abs/10.1111/j.1540-6261.2012.01740.x) | [Internet appendix](https://afajof.org/wp-content/uploads/files/supplements/Decoding_Inside_Information-.pdf)
- Lakonishok, Lee (2001). [Oxford RFS](https://academic.oup.com/rfs/article-abstract/14/1/79/1587398) | [LSV PDF](https://www.lsvasset.com/pdf/research-papers/Insider-Trades-Informative.pdf)
- Seyhun (1986, 1998). [MIT Press book](https://mitpress.mit.edu/9780262692342/investment-intelligence-from-insider-trading/)
- Brochet (2010). [SSRN 1108731](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=1108731) | [HBS](https://www.hbs.edu/faculty/Pages/item.aspx?num=36909)
- Jagolinzer (2009). [SSRN 541502](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=541502) | [INFORMS](https://pubsonline.informs.org/doi/10.1287/mnsc.1080.0928)
- Larcker, Lynch, Quinn, Tayan, Taylor (2021), "Gaming the System." [Harvard Corp Gov](https://corpgov.law.harvard.edu/2021/01/28/gaming-the-system-three-red-flags-of-potential-10b5-1-abuse/) | [Stanford GSB](https://www.gsb.stanford.edu/faculty-research/publications/gaming-system-three-red-flags-potential-10b5-1-abuse)
- Kim, Kim, Rajgopal (2025), "Insider Trading After the 2022 Rule 10b5-1 Amendment." [SSRN 5362431](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=5362431) | [CLS Blue Sky](https://clsbluesky.law.columbia.edu/2025/07/31/insider-trading-after-the-2022-rule-10b5-1-amendment/)
- Ali, Hirshleifer (2017). [RePEc](https://ideas.repec.org/a/eee/jfinec/v126y2017i3p490-515.html) | [UCI](https://sites.uci.edu/dhirshle/abstracts/opportunism-as-a-managerial-trait-predicting-insider-trading-profits-and-misconduct/)
- Rogers, Van Buskirk, Zechman (2011), "Disclosure Tone and Shareholder Litigation." [SSRN 1331608](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=1331608)
- Alldredge, Cicero (2019), "Do Insiders Cluster Trades With Colleagues?" [Wiley JFR](https://onlinelibrary.wiley.com/doi/abs/10.1111/jfir.12172)
- Hoberg, Lewis (2017), "Do Fraudulent Firms Produce Abnormal Disclosure?" [SSRN 2298302](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=2298302)
- Biggerstaff, Cicero, Wintoki (2020), "Insider Trading Patterns." [Wichita PDF](https://www.wichita.edu/academics/business/accountancy/documents/InsiderTradingPatternsWintokiNov2016.pdf) | [JCF](https://www.sciencedirect.com/science/article/abs/pii/S0929119920300985)
- Insider trading before accounting scandals (2015). [ScienceDirect S0929119915000784](https://www.sciencedirect.com/science/article/abs/pii/S0929119915000784)
- Aalto Master's Thesis (2025), CMP replication 2008–2024. [Aalto](https://aaltodoc.aalto.fi/server/api/core/bitstreams/fbbd1ec6-d5b4-44dd-881d-144ffd0ea21c/content)
- Zhao (2025), "Insider Purchase Signals in Microcap Equities." [arXiv 2602.06198](https://arxiv.org/pdf/2602.06198)
- IFD Benchmark (2025). [arXiv 2507.20162](https://arxiv.org/html/2507.20162v1)

## SEC Primary Sources
- SEC press release on Dec 14, 2022 amendments. [SEC 2022-222](https://www.sec.gov/newsroom/press-releases/2022-222)
- SEC small-business compliance guide on 10b5-1. [SEC](https://www.sec.gov/resources-small-businesses/small-business-compliance-guides/insider-trading-arrangements-and-related-disclosures)
- SEC Form 4 and Forms 3/4/5 instructions. [Form 4 PDF](https://www.sec.gov/files/form4.pdf) | [Form 4 data PDF](https://www.sec.gov/files/form4data,0.pdf) | [Investor Bulletin](https://www.sec.gov/files/forms-3-4-5.pdf)
- SEC Ownership Form Codes. [SEC](https://www.sec.gov/edgar/searchedgar/ownershipformcodes.html)
- SEC Section 16 overview. [SEC](https://www.sec.gov/resources-small-businesses/going-public/officers-directors-10-shareholders) | [17 CFR §240.16a-2](https://www.law.cornell.edu/cfr/text/17/240.16a-2)
- EDGAR Ownership XML Technical Specification. [SEC PDF](https://www.sec.gov/info/edgar/ownershipxmltechspec-v3.pdf)
- SEC EDGAR rate limits. [SEC](https://www.sec.gov/filergroup/announcements-old/new-rate-control-limits) | [SEC](https://www.sec.gov/search-filings/edgar-search-assistance/accessing-edgar-data)
- SEC EDGAR filing counts by form type. [SEC](https://www.sec.gov/data-research/sec-markets-data/number-edgar-filings-form-type)

## Library / Tooling
- edgartools. [GitHub](https://github.com/dgunning/edgartools) | [readthedocs](https://edgartools.readthedocs.io/)
- sec-edgar-downloader. [readthedocs](https://sec-edgar-downloader.readthedocs.io/)
- py-sec-edgar. [GitHub](https://github.com/ryansmccoy/py-sec-edgar)
- The Washington Service. [washingtonservice.com](https://www.washingtonservice.com/all-products/us-insider-trading/) | [LSEG](https://www.lseg.com/en/data-analytics/financial-data/news/washington-service)
- OpenInsider. [openinsider.com](http://openinsider.com/)

## Law-Firm / Practitioner Summaries (Dec 2022 amendments, blackout policy survey)
- Skadden alert on amendments. [Skadden](https://www.skadden.com/insights/publications/2022/12/sec-amends-rules-for-rule-10b51-trading-plans-and-adds-new-disclosure-requirement)
- Morgan Lewis. [Morgan Lewis](https://www.morganlewis.com/pubs/2022/12/sec-adopts-significant-changes-to-rule-10b5-1-affecting-trading-by-insiders)
- A&O Shearman. [aoshearman.com](https://www.aoshearman.com/en/insights/sec-changes-requirements-for-rule-10b51-plans)
- Clifford Chance. [Clifford Chance briefing](https://www.cliffordchance.com/briefings/2022/12/sec-adopts-amendments-to-rule-10b5-1-imposing-cooling-off-period.html)
- Wilson Sonsini SV150 insider-trading-policy survey 2025. [WSGR PDF](https://www.wsgr.com/a/web/bPTkLm9NChAxLS7DiWkjfv/wilsonsonsini_insider_trading_report_20251111.pdf)
- Orrick / NASPP / Perkins Coie blackout overviews. [Orrick](https://www.orrick.com/en/Insights/2024/06/Insider-Trading-Policy-Key-Terms-and-Trends) | [NASPP](https://www.naspp.com/blog/4-Trends-in-Trading-Blackout-Periods) | [Perkins Coie](https://perkinscoie.com/public-company-handbook-chapter-6-insider-reporting-obligations-and-insider-trading-restrictions)