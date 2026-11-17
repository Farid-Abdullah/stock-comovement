# Study guide for the presentation and oral exam

This guide is for the three of us. The oral exam is worth twice the presentation, and the professor will ask named people to open the code, explain a figure, or reason about something we never ran. Read this end to end once, then take turns explaining each section to each other with the notebook open.

**Files you must be able to open quickly:**

| What | Where |
|---|---|
| The whole analysis | `final_project.ipynb` (run all: about 3 minutes) |
| Every figure and table | `outputs/final/` (`key_numbers.json` holds every number in the slides and report) |
| Bigger-font slide versions of 4 figures | `outputs/final/slides/` (made by `make_slide_figures.py`) |
| Report source | `report/main.tex` + `report/refs.bib` + `report/figures/` (upload the folder to Overleaf) |
| Earlier yearly analysis (step 1) | `comovement_association_rules.ipynb` |

---

## 1. The story in two minutes

1. **Question.** Our proposal asked whether ChatGPT changed which stocks move together. The feedback said: you can't tell ChatGPT from the market, your stock list might decide the answer, and the project should be harder and include prediction.
2. **Fix 1: remove the market.** Before mining, each stock's return is replaced by its *residual*: the part the market does not explain. Without this, rules mostly say "the market crashed" (Fig 4.1).
3. **Fix 2: test ChatGPT against fake dates.** We measure how much co-movement changed around every month from 2017 to 2025. ChatGPT's month is ordinary (ranks above only 21–62% of the 107 dates). So **we falsified our own hypothesis**. With raw returns ChatGPT would have looked special (91st percentile): that is the market trap.
4. **Fix 3: let the data regroup the stocks.** What *did* change is who moves with the chip stocks. Oracle and Caterpillar joined; software stocks left; by 2026 software and chips co-move *less* than chance (Fig 5.1, 6.2).
5. **Prediction serving the patterns.** For each mined rule we predict whether it will be found again in the next six months. Old rules and rules inside one group last; lift (the usual ranking) is a weak guide (Fig 7.1, 7.2).
6. **Shock days.** An Isolation Forest finds unusual days without hand-tagging. Nvidia's May 2023 guidance and DeepSeek are in the top 1%; ChatGPT's launch day is not.

**Data mining rationale (say it in these words):** pattern discovery (rules, clusters, anomalous days) plus analysis of the method (how the rules react to the return definition, thresholds and algorithm). The prediction's target is a mined rule, so if you delete every accuracy number, the findings still stand.

---

## 2. Concepts in plain words

### Finance

- **Daily return**: today's price / yesterday's price − 1. We use *adjusted* closes so splits and dividends don't look like moves.
- **The market / SPY**: SPY is an ETF that tracks the S&P 500. We use its return as "what the market did today".
- **Beta (β)**: how strongly a stock usually follows the market. β = 1.2 means on a day SPY falls 1%, the stock "normally" falls 1.2%. NVDA's β was 1.18 at the start of 2016. We estimate it from the previous 252 days (one trading year) with `cov(stock, SPY) / var(SPY)`.
- **Residual return**: `stock return − β × SPY return`. The part of the move that is about the stock or its industry, not the market. This is the "market model" from event studies (MacKinlay 1997).
- **Excess return**: `stock return − SPY return` (β fixed at 1). Simpler, but leaves market exposure in high-β stocks. We ran it as a comparison.
- **Volatility**: standard deviation of returns. We use each stock's own residual volatility over the previous 60 days.
- **Survivorship bias**: we picked 40 companies that still exist in 2026. Companies that collapsed are missing, which can make patterns look cleaner than they were.

### Data mining

- **Basket / transaction**: one trading day. **Item**: `NVDA_UP` or `NVDA_DOWN`. 40 stocks × 2 directions = 80 possible items. On average 9.6 items per day.
- **Major move**: z = residual / (60-day residual volatility). Item if z ≥ 1 (UP) or z ≤ −1 (DOWN). Roughly 12% of days per item.
- **Support** of an itemset: share of days it appears. 0.04 of 252 days ≈ 10 days.
- **Confidence** of A → C: P(C | A) = support(A∪C) / support(A).
- **Lift** of A → C: confidence / support(C) = how many times more often A and C happen together than if independent. 1 = chance; 2 = twice as often.
  - In our data an item's support is about 0.12, so a confidence of 0.4 already implies a lift of about 3.3. That is why the lift ≥ 1.5 threshold rarely binds. The median lift of our mined rules is 3.97 (10th–90th percentile 2.7–6.0).
- **Pair lift** (heatmaps, group lines, AI affinity): lift of "stocks i and j made a major move in the *same direction* on the same day" = (share of days both UP + share both DOWN) / (expected share if independent).
- **Apriori**: finds frequent itemsets level by level (size 1, then 2, then 3), generating candidates and counting them. **FP-Growth**: compresses all baskets into one prefix tree once, then grows itemsets from it without generating candidates. Both give *identical* itemsets.
- **Jaccard similarity** of two sets: |A ∩ B| / |A ∪ B|. Jaccard *distance* = 1 − similarity. Used for (a) rule turnover between two rule sets and (b) distance between two stocks' move records.
- **Hierarchical clustering (average linkage)**: start with every stock alone; repeatedly merge the two clusters with the smallest *average* distance between their members; cut the tree into 4 clusters.
- **Spectral clustering**: treat stocks as nodes of a graph with similarity as edge weight; find the cut that separates groups with few strong links between them. Good at non-round cluster shapes.
- **Adjusted Rand Index (ARI)**: agreement between two groupings, corrected for chance. 1 = identical; 0 = random.
- **Shuffle test**: shuffle each item column independently. Each stock keeps its number of UP/DOWN days, but links between stocks are destroyed. Rules that still appear are chance.
- **Fisher exact test / hypergeometric tail**: if A happened on n_A of N days and C on n_C, what is the probability that they overlap on at least n_AC days by chance? Small p = real association.
- **False discovery rate (Benjamini–Hochberg)**: when testing many hypotheses, controls the expected share of false positives among the ones you call significant. Sort p-values; the k-th smallest passes if p ≤ q·k/m, where m = number of tests. **We set m = 480,480, all rules the miner could have returned**, not just the ones it kept.
- **Block bootstrap**: resample blocks of 10 consecutive days with replacement to build a new "fake year" many times; the spread of the statistic across resamples gives a confidence interval. Blocks (not single days) keep short bursts of related days together.
- **Placebo test**: apply the same measurement at many dates where nothing special happened; the real date should stand out if the effect is real.
- **ROC-AUC**: the probability that a randomly chosen surviving rule gets a higher score than a randomly chosen dying rule. 0.5 = coin flip.
- **PR-AUC (average precision)**: area under precision–recall; its no-skill level equals the base rate (0.36 in our test set).
- **Precision@20%**: of the 20% of rules the model trusts most, the share that actually survive.
- **Permutation importance**: shuffle one feature in the test set; the drop in ROC-AUC is how much the model relied on it.
- **Isolation Forest**: builds random trees that split the data on random features at random values. Unusual points get isolated in few splits, so a short average path length means an anomaly.

---

## 3. Walking through the notebook

The cell numbers below are the order in the notebook. Search for the function name with Ctrl+F.

### Section 1: Settings
All parameters in one cell. Be ready to justify each:

| Setting | Value | Why |
|---|---|---|
| `STUDY_START` | 2016-01-01 | 2014–15 is needed to estimate the first betas (252 days) and volatilities (60 days) |
| `MAIN_MODE` | `residual` | removes the market, including extra exposure of high-β stocks |
| `BETA_WINDOW` | 252 | one trading year: long enough for a stable β, short enough to adapt |
| `VOL_WINDOW` | 60 | about three months: "typical move size" that adapts to calm and stormy periods |
| `Z_K` | 1.0 | about 12% of days per item: enough items per basket to mine with 252 baskets. 1.5 tested in 5.4 |
| `WINDOW` / `STEP` | 252 / 21 | one year of baskets per rule set, moved one month at a time → 120 windows |
| `MIN_SUPPORT` | 0.04 | ≈10 days a year. The proposal's 0.05/0.5 left ≈25 residual rules per year, too few to compare |
| `MIN_CONFIDENCE` / `MIN_LIFT` | 0.4 / 1.5 | see the lift note above: confidence 0.4 already implies lift ≈ 3 |
| `MAX_LEN` | 3 | rules with 2 or 3 items; longer rules have support too small to trust in 252 baskets |
| `CHATGPT_DATE` | 2022-12-01 | first trading day after the 30 Nov 2022 release (US afternoon). Also keeps the Powell-speech rally of 30 Nov in the "before" year |
| `FUTURE_DAYS` | 126 | half a year: long enough that "survives" means something, short enough for many labelled windows |

### Section 2: Data — `load_prices`
Reads `data/prices.csv` (downloaded once by the step 1 notebook with `yfinance`, `auto_adjust=True`). Raises an error if a ticker is missing. 3,134 days × 41 tickers, no missing prices.

### Section 3: Preprocessing
- **`market_model_residuals(returns, market, window)`**: for each stock, `rolling(window).cov(market) / market.rolling(window).var()` gives β, then `.shift(1)` so day t's β uses days t−252..t−1 only. Returns `returns − β × market`.
- **`find_major_moves(returns, z_k, vol_window)`**: `typical_move = returns.rolling(60).std().shift(1)`; `score = returns / typical_move`; UP if score ≥ z_k, DOWN if ≤ −z_k. Returns the True/False basket table (80 columns) and the scores.
- The basket-statistics table shows raw returns give 336 days with 20+ items vs 126 for residuals: big baskets are market days.

### Section 4: Rolling mining
- **`mine_rules(basket, ...)`**: runs `fpgrowth` (or `apriori`), then `association_rules(..., metric="confidence", min_threshold=0.4)`, keeps lift ≥ 1.5, and adds descriptive columns: `n_items`, `n_groups` (how many of our 4 groups the rule's stocks belong to), `cross_group`, `has_baseline`, `has_ai`, `direction` (all UP, all DOWN, or MIXED).
- **`window_ends(n_days, window, step)`**: row positions of each window's last day; the last window always ends on the last day.
- **4.1 loop**: mines every window under all three modes; keeps full rule tables only for `residual` (raw would be millions of rows). Computes Spearman correlation between rule count and SPY volatility per mode.
- **4.2**: FP-Growth vs Apriori: same itemsets; timing table.
- **4.3** `shuffle_items`, `rule_p_values`, `benjamini_hochberg`: see concepts. `N_POSSIBLE_RULES = C(40,2)·4·2 + C(40,3)·8·6 = 480,480`. Pairs: 780 stock pairs × 4 direction combinations × 2 orientations (A→C and C→A). Triples: 9,880 stock triples × 8 direction combinations × 6 ways to split 3 items into antecedent → consequent (3 with one item on the left, 3 with two).

### Section 5: ChatGPT
- **`pair_lift_matrix(basket)`**: matrix algebra version of pair lift. `up.T @ up` counts days both were UP for every pair at once.
- **`block_means(lift)`**: average pair lift inside each group and between each pair of groups (10 blocks).
- **`break_statistics(its, pos, span)`**: mines the 252 days before and after position `pos`, returns the four measures (rule turnover; tech change minus control change; AI–AI change minus control change; AI–software change). The `log2` with `clip(0.25, 8)` makes doubling and halving count the same and stops pairs with tiny counts from exploding.
- **`candidate_break_positions`**: first trading day of each month with 252 days on both sides → 107 dates.
- **`percentile_of(table, date, col, two_sided)`**: share of dates whose value is ≤ ChatGPT's. For signed measures we compare sizes (`abs`).
- **5.4 robustness**: the same percentiles under 7 settings (Table I in the report).

### Section 6: AI category
- **AI affinity**: `np.nanmean(L[:, ai_idx], axis=1)`: each stock's mean pair lift with the ten AI enablers (its own NaN diagonal is ignored).
- **`block_bootstrap`, `ai_affinity`**: 500 resamples of 10-day blocks for three 504-day periods; the change "latest − pre" gets a 95% interval and a two-sided bootstrap p-value; BH across 40 stocks.
- **`move_records`, `cluster_window`**: Jaccard distance between stocks' [UP days, DOWN days] vectors; average-linkage hierarchical and spectral (`affinity="precomputed"` on 1 − distance), both k = 4. ARI vs our groups; also which stocks share NVDA's spectral cluster before ChatGPT vs from Dec 2023.

### Section 7: Rule survival
- **`joint_days`**: True on the days a rule's items all appear.
- **`future_holds`**: recomputes support, confidence and lift on the next 126 baskets and checks all three thresholds.
- The record loop builds one row per (window, rule) with all features. `age` counts back through consecutive previous windows; `seen_last_12` counts appearances in the last 12; `burstiness = max joint days in any 21-day block / total joint days`; `shock_share` uses a *past-only* threshold (95th percentile of basket size over the previous year, shifted by one day).
- **Split**: train = windows whose future period ends before ChatGPT (8,202 rules); test = windows ending after ChatGPT (5,215). The windows in between (whose future crosses ChatGPT) are left out so no label leaks.
- **`precision_at`, `evaluate`**: metrics; models and one-feature baselines; permutation importance; rolling-origin loop (train on all labels known before each year, test on that year).
- **7.5**: model trained on all labels scores the latest window's 2,097 rules: most durable (AMAT↔LRCX, ASML–LRCX, ACN↔CTSH) and strong-but-fragile (e.g. `MSFT_DOWN, SAP_DOWN → CAT_UP`, a 2026 rotation pattern).

### Section 8: Shock days
- `IsolationForest(n_estimators=300, contamination=0.01)` on residual z-scores (clipped ±10). `anomaly = −score_samples` so higher = more unusual. Compared with basket size (Jaccard 0.50 between their top 1% days). `describe_day` lists the six largest residual moves.

### Section 9: Summary
`to_jsonable` converts numpy types so `key_numbers.json` can be written.

---

## 4. Figure by figure

For each: what produced it → how to read it → the number to quote → what it means for a decision maker.

- **4.1 Rules per window by mode** (`4_1_...png`, section 4.1 loop). Lines = rule counts per window for raw/excess/residual (log scale); grey panel = SPY volatility. Quote: median 3,905 raw vs 118 residual; Spearman 0.71 vs 0.37. Meaning: raw rules measure market volatility; anyone mining raw co-movement would "discover" crashes.
- **4.3 Chance test** (section 4.3). Real vs FDR-significant vs shuffled rule counts. Quote: shuffled 67 rules vs 24,585 real (0.3%); 82% significant. Meaning: the rules are not search artefacts. The 2026 spike is real co-movement (the software block).
- **5.1 Group lift over time** (section 5.1). Left: within-group; right: between groups. Quote: software–software 1.47 → 2.77; AI–software 1.23 → 0.58 (year to Nov 2022 vs year to Nov 2026). Meaning: software now trades as its own block, opposite to chips.
- **5.2 Placebo test** (section 5.2). Each dot = one candidate break date, value = change between year before and year after; red = ChatGPT. Quote: ChatGPT above 62/29/36/21% of dates. Meaning: no evidence ChatGPT re-wired co-movement on release; the big re-wiring is around 2025–26.
- **6.1 AI affinity heatmap** (section 6.1). Rows = stocks (coloured by group), columns = windows; red = moves with chips more than chance, blue = less. Look at ORCL turning red after 2023, CAT turning red in 2025–26, software turning blue in 2026.
- **6.2 Affinity change** (section 6.2). Dot = change (latest 2 years − 2 years before ChatGPT); bar = 95% bootstrap interval; outlined = significant after FDR. Quote: ORCL +1.06, CAT +0.81; 14 significant fallers. Meaning: "diversified" portfolios mixing chips, Oracle and Caterpillar are one AI bet.
- **6.3 Clusters** (section 6.3). Left: ARI with our groups over time for two methods; right: share of windows each stock sits in NVDA's spectral cluster. Quote: spectral ARI 0.35 → 0.54; ORCL 7% → 49%; INTC 61% → 3%. Spectral beats hierarchical in 92.5% of windows.
- **7.1 Survival by feature** (section 7.1). Bars = share of rules mined again next half-year. Quote: age 12+ 58% vs new 21%; one group 37% vs linking groups 10%. Meaning: trust old, within-group rules.
- **7.2 Models** (section 7.2). Blue = models, grey = baselines. Quote: RF 0.66, LR 0.65, lift 0.58, age 0.63; LR top-20% precision 0.64 vs base 0.36.
- **7.3 Importance** (section 7.3). Left: permutation importance (RF); right: logistic coefficients (green raises survival). Quote: `n_groups` first. Caution: coefficients of correlated features (age vs seen_last_12; lift vs conviction) split credit, so read signs of correlated features with care.
- **7.4 Rolling origin** (section 7.4). Models beat lift every year 2020–2026; in 2019 they lose (little training data, only 2017–18 labels).
- **8.1 Anomaly timeline** (section 8). Grey = daily score, blue = 5-day average, dotted = top 1%. Quote: DeepSeek 99.6th, Nvidia guidance 99.3rd, ChatGPT 68th percentile.

---

## 5. Questions to expect, with answers

### Implementation
- **"Open the function that builds the baskets."** `find_major_moves` in section 3. Walk through: rolling std shifted by one day, divide, compare with ±Z_K, rename columns, concatenate UP and DOWN.
- **"Why `.shift(1)`?"** So the β and volatility used to judge day t are computed from days before t. Without it, today's own return would be part of the yardstick (look-ahead).
- **"Why is 480,480 the number of tests?"** See section 3 above (pairs 6,240 + triples 474,240).
- **"How is `age` computed?"** Count back through consecutive previous windows (21 days apart) that contain exactly the same rule string; stop at the first window that does not.
- **"Why are some windows left out of the survival train and test sets?"** Their 126 future days straddle ChatGPT, so putting them in training would leak post-ChatGPT information into the training labels.

### Justification
- **"Why association rules and not correlation?"** Correlation is linear and dominated by the size of returns, so a few extreme days drive it. Rules count *days* of large moves (one extreme day counts once), handle combinations of 3 stocks and directions (UP with DOWN), and give support/confidence/lift that are easy to interpret. Correlation clustering (Mantegna 1999) is the natural cross-check, which is why we also cluster.
- **"Why residual and not excess returns?"** Excess assumes β = 1. A high-β stock still falls more than SPY on a down day, so excess returns leave market days in the data. Residuals use each stock's own β.
- **"Why rolling windows instead of before/after?"** Two periods give one comparison with nothing to compare it to. 120 windows let us date changes and run a placebo test.
- **"Why FP-Growth if Apriori was faster?"** Honest answer: at our size (≤3 items) Apriori is faster in mlxtend (8.5 ms vs 25.7 ms). FP-Growth wins when itemsets get longer (≤5 items on the raw 2020 window: 3.9 s vs 13.1 s). They give identical results, so the choice does not change any finding; FP-Growth scales better if `MAX_LEN` rises or support falls.
- **"Why spectral and hierarchical?"** Two different ideas of a cluster: compact groups vs graph cuts. Agreement between them (ARI 0.34–0.44) and with our labels tells us how real the groups are. Spectral matched our labels better in 92.5% of windows.
- **"Why these models?"** Logistic regression for readable signs, random forest and gradient boosting for non-linear effects. Baselines are single features so we can see what the model adds beyond the obvious.

### Interpretation
- **"This lift is 2.3. Is that big here?"** For a single mined rule, no: the median lift of our mined rules is about 4, because confidence ≥ 0.4 with item support ≈ 0.12 forces lift ≈ 3+. For a *group average pair lift*, yes: 1 is chance, within-AI averages 2–2.8, and the control group's link to AI is about 0.7–0.8.
- **"ChatGPT ranks above 62% of dates on turnover. Why isn't that evidence?"** 62% means 38% of ordinary months show *more* change. Our pre-stated bar was 90%.
- **"Why is AI–software lift below 1?"** Below 1 means they make same-direction big moves *less* often than chance: in 2026 software tended to fall on days chips rose (the "AI threatens software" trade), after removing the market.
- **"Does ROC-AUC 0.66 mean the model is good?"** Moderately. It ranks a survivor above a non-survivor two times in three. The finding is less the model than the comparison: lift is near-useless (0.58) while history and scope carry the signal.

### Counterfactual (things we never ran)
- **"If we doubled the number of years?"** Each window still has 252 baskets, so per-window rule counts and thresholds behave the same. We would get more placebo dates (finer ranks) and more labelled rules for survival training (probably better 2019-style early years). The ChatGPT result would not change because it depends on the same windows around 2022.
- **"If we doubled the number of stocks?"** 160 items; possible rules grow about 8× (triples dominate), so the FDR correction becomes stricter and mining slower (still seconds). More rules overall, and a much better map of the AI category.
- **"If support were 0.02?"** Rules supported by ~5 days pass. Many more rules, and the shuffle test would find many more chance rules (two items with support 0.12 overlap on about 3.6 days by chance, so 5 is easy to reach by luck). The significant share falls, and survival rates fall because weak rules rarely repeat.
- **"If Z_K were 2?"** A move needs 2σ: each item (one direction) appears on roughly 2–3% of days instead of 12%, baskets shrink to about 2 items, and pair supports become tiny. We would have to lower support a lot, rules would be fewer and noisier (the z = 1.5 row of Table I already shows unstable percentiles).
- **"If the window were 6 months?"** Half the baskets: support counts halve, lift estimates get noisier, rule turnover rises everywhere. Our half-year row shows the ChatGPT conclusion still holds on tech change (29%).
- **"If STEP were 1 day?"** About 2,500 windows that are almost identical: no new information, much more autocorrelation, and the survival dataset would be mostly duplicates.
- **"If you used raw returns for survival?"** Many rules would be market-crash rules that appear together and vanish together with volatility, so survival would track the volatility regime (`spy_vol` would dominate importance).
- **"What would make the Oracle finding disappear?"** If it came from a few extreme days, block resampling would make the interval cross zero. It does not, and because items count days, ORCL's +36% day on 10 Sep 2025 counts as one day, the same as a 2σ day.

---

## 6. What we tried and dropped (the rubric asks about removed code)

1. **Two halves (proposal) → yearly windows (step 1 notebook) → rolling windows.** On residual moves the yearly rule sets were too small (calendar 2019 gave only 4 rules at support 0.05 and confidence 0.5), so we moved to rolling windows and support 0.04.
2. **Raw returns as main setting → residuals.** Kept raw and excess as comparisons (Fig 4.1, Table I).
3. **FDR over only the mined rules.** Our first version applied Benjamini–Hochberg only to the rules that passed the thresholds and found 100% significant. That ignores the search: the miner looked at 480,480 possible rules. Corrected to m = 480,480 → 82%.
4. **`cross_group` as a survival feature.** It is the same information as `n_groups > 1`; with both in, logistic regression gave them opposite signs. Removed from the features (still used for the descriptive Fig 7.1).
5. **"FP-Growth is faster" claim.** Our timing showed the opposite at our settings; the notebook now says so.
6. **The event-tagging redesign** (hand-tagging 150–200 events and predicting the top 5 stocks after each). Dropped because tagging is subjective, events chosen with hindsight bias the result, most tag combinations would have only 2–5 events, and on event days most stocks simply follow the market. Its good idea, studying events, survives as the Isolation Forest shock-day analysis.

---

## 7. Honest weaknesses (say them before you are asked)

- 40 hand-picked survivors; only 10 AI stocks.
- One-factor market model: sector/style factors remain in residuals (partly why within-group lift is high).
- Overlapping windows → placebo ranks and survival samples are dependent; we report ranks, not p-values.
- Survival model only slightly beats "rank by age".
- 2026 is a partial year, and the 2026 software block is recent; it might not last.

---

## 8. Suggested split for the talk and preparation

| Person | Presents | Must master (and can explain the others') |
|---|---|---|
| Farid | slides 1–4: question, data, method | Sections 1–4 of the notebook, `find_major_moves`, `mine_rules`, thresholds, FP-Growth vs Apriori |
| Muzayyan | slides 5–9: market removal, ChatGPT test, AI category | Sections 4.3–6: shuffle/Fisher/FDR, `break_statistics`, placebo, bootstrap, clustering |
| Mohamad | slides 10–14: survival, shock days, limits, takeaways | Sections 7–8: survival labels and features, train/test split, metrics, Isolation Forest |

Then swap: each person explains one figure from someone else's part, out loud, with the code open.

**Before the exam:** run `final_project.ipynb` once on the presenting laptop (`pip install -r requirements.txt`), keep `outputs/final/` open in a file browser, and keep this guide's section 5 at hand.
