# DETAILS: our notes on the project

For the three of us: the story we are telling, the numbers behind it, every data mining concept we use (with where
it sits in the course), and the questions we should expect. Numbers are from the fresh S&P 100 run of 22 Nov 2026
(`outputs/rules/key_numbers.json`, `outputs/events/key_numbers_events.json`).

---

## 1. The story in plain words

**The question.** Stocks rise and fall together in habits. Which news events actually change those habits, and when
they do, does the change stick?

**The cafeteria analogy.** Think of a school cafeteria.

* **Who sits with whom is the co-movement pattern.** Friends who sit together every day are stocks that make big
  moves together: Nvidia with AMD, JPMorgan with Bank of America, Coca-Cola with PepsiCo. Some pairs avoid each
  other (when oil jumps, oil producers go up while airlines go down).
* **The whole room standing up when the bell rings is the market.** If everyone stands at once, that tells you about
  the bell, not about friendships. That is why we remove the market first (Q0): otherwise every crash day looks like
  "all 100 stocks are best friends".
* **A fire drill is a one-off shock.** One lunch is chaos and everyone is in the wrong seat: an *unusual day*. The
  next day most people are back with their usual friends, so there was **no break**.
* **A new principal with new rules is a lasting break.** Seating changes and stays changed.
* **A rule that applies to one table** (only the bank table cares about interest rates) is **who reacts** (Q2).
* **A friend group that forms slowly over a year, with no single cause,** is what happened around the chip stocks:
  Oracle and Caterpillar started "sitting with" the semiconductor stocks, and the chip stocks themselves split up.
* **Friendships that are years old and inside one class** are the ones that last. That is the prediction: old,
  within-sector rules survive; new, cross-sector ones fade.

**Why anyone cares.** A fund manager diversifies by owning stocks that do *not* move together. If an event quietly
makes two "unrelated" stocks start moving together, the portfolio is riskier than it looks. So: which events rewire
who moves with whom, should a manager react to every big news day, and which patterns can be trusted?

**How we got here.** The proposal asked whether ChatGPT changed co-movement. The professor asked how we would know it
was ChatGPT and not the market or the hundred other things happening. So we stopped assuming one date matters and
test every dated event the same way, against chance. We also replaced our 40 hand-picked stocks with the S&P 100,
because "your choice of stocks can decide your result" was a fair criticism.

**The short answer (from the data).**

1. Removing the market matters most: raw-return rules are mostly the market moving.
2. Events explain the strangest days only when we pick the events by hand. Scheduled news (Fed, inflation, jobs)
   matches no more unusual days than chance.
3. Fed days are a bit busier for most sectors (about 1.2× the usual rate of big moves); inflation and jobs days are not.
4. Earnings pull the company's own sector, but less than an ordinary big move does.
5. Big shocks rarely line up with structure breaks. Of 15 shocks we could follow for two years, 10 left no break,
   2 left a lasting change, 2 (both COVID) left a break that healed, 1 is in between. These counts move with the
   settings, so they are suggestive.
6. The lasting change we do see built up slowly around the chip stocks, not on one event day.
7. Rules that last are old and stay inside one sector; lift says almost nothing about durability.

---

## 2. The questions and the current answers

| Question | Method | Result | Verdict |
|---|---|---|---|
| **Q0** Real co-movement or the market? | Raw vs excess vs residual returns; shuffle test; Fisher + Benjamini-Hochberg | Median pair rules per window: raw 2,461, residual 421. Rank correlation of rule count with market volatility: raw 0.74, residual 0.42. Shuffled data gives 0.26% of the real rules; 77% of rules are significant | Real, once the market is removed |
| **Q1** Do events explain the strangest days? | Isolation Forest top 1% (27 days); event-date shift test (1,000 shifted calendars) | 33% of unusual days match an event vs 14% by chance (p = 0.002), all from the hand-picked shocks (33% vs 2%). Scheduled releases: 7% vs 13% (p = 0.93). Categories: 9 shock, 6 earnings reaction, 7 market stress (March 2020), 1 earnings day with a quiet reporter, 4 unexplained | Only for hand-picked shocks |
| **Q2** Who reacts? | Move ratio by sector with bootstrap intervals; Mann-Whitney; events as items; earnings spillover | Fed days: Tech 1.17, Financials 1.20, Industrials 1.18, Comms 1.24, Semis 1.21 (all intervals above 1). CPI and jobs days: nothing. Earnings: own-sector spillover 1.43 vs 1.86 after ordinary moves; 19 of 3,668 earnings rules significant, all stronger than on ordinary days | Fed days modestly; CPI/jobs no; earnings yes but weaker than ordinary moves |
| **Q3** Does the change last? | Weekly break score + shifted shock dates; recovery curves vs normal drift | Shocks at the 57th break percentile vs 50% (p = 0.19). Recovery: 10 no break, 2 lasting (2016 election, Feb 2018 volatility spike), 2 temporary (both COVID dates), 1 partial (2018 tariffs). Robustness: z = 1.5 gives 3 temporary / 3 lasting; raw gives 5 / 0 | Breaks are rare; whether they last depends on settings |
| **Prediction** Which rules last? | Logistic regression, random forest, gradient boosting vs one-feature baselines; train before Dec 2022, test after | ROC-AUC 0.79-0.80 vs 0.52 (rank by lift), 0.70 (rank by age). Age 12+ windows: 58% survive vs 14% for new rules; same sector 38% vs cross-sector 8% | History and scope predict durability; lift does not |

AI events (single days, anomaly percentile): ChatGPT 60th, GPT-4 59th (ordinary days); Nvidia's guidance 98th,
DeepSeek 99.5th, Oracle's backlog 92nd. None of the AI events left a lasting break in the whole structure.

---

## 3. The pipeline

1. **`stocks.ipynb`**: what the S&P 100 is, the 100 companies and their sectors, price download, data checks,
   sector charts. Writes `data/prices.csv`, `data/stocks.csv`.
2. **`comovement_rules.ipynb`**: prices → residual returns → major moves → daily baskets → rules on 120 rolling
   windows → chance tests (Q0) → sector and semiconductor co-movement → rule-survival prediction → unusual days.
3. **`events.ipynb`**: event calendar (with reasons and sources) and earnings → Q1 (unusual days vs events) →
   Q2 (who reacts) → Q3 (breaks and recovery) → robustness.

---

## 4. Data mining concepts, in a few words, mapped to the course

Lecture numbers come from the course section guide (Lecture 01 Introduction, 02 Frequent itemsets and association
rules, 03 Preprocessing (sampling, TF-IDF), 04 Classification, 05 Regression, 06 Feature selection and
dimensionality reduction, 07 Clustering, 08 Anomaly detection, 09 Sentiment analysis, 10 Topic modelling, 11 Graph
mining, 12 Sequence and time-series mining). Chapters are from the textbook, Zaki & Meira, *Data Mining and Machine
Learning*, 2nd ed.; the chapter numbers are from the book's table of contents as we know it, so check them against
the slides.

### Preprocessing (Lecture 03; textbook Ch. 2 numeric attributes)

| Concept | In a few words | Where we use it |
|---|---|---|
| Daily return | Percent change from yesterday's close | All notebooks |
| Adjusted close | Price corrected for splits and dividends, so a split is not a crash | `stocks.ipynb` §4 |
| Market model, beta | Beta = slope of a stock's return on the market's return (a linear regression, Lecture 05, Ch. 23), estimated on the previous 252 days only | `comovement_rules.ipynb` §3 |
| Residual return | Return minus beta × market return: the stock's own move | §3 |
| z-score normalisation | Today's residual divided by the stock's own volatility (last 60 days), so quiet and jumpy stocks are judged fairly | §3 |
| Discretisation into items | z ≥ 1 → `TICKER_UP`, z ≤ −1 → `TICKER_DOWN`: numbers become items for rule mining | §3 |
| Transaction / basket | One trading day = the set of items that happened that day (100 stocks × 2 = 200 possible items; 24 per day on average) | §3 |
| No look-ahead | Beta and volatility use only past days, so nothing from the future decides today's item | §3 |

### Frequent itemsets and association rules (Lecture 02; Ch. 8 itemset mining, Ch. 12 pattern and rule assessment)

| Concept | In a few words | Where we use it |
|---|---|---|
| Itemset, support | A set of items; support = share of baskets containing all of them (0.04 = about 10 days a year) | §4 |
| Association rule A → B | "If A is in the basket, B tends to be too", e.g. `{AMAT_UP} → {LRCX_UP}` | §4 |
| Confidence | Share of A's days that also have B (we require 0.4) | §4 |
| Lift | Confidence divided by how often B happens anyway; 1 = chance, 2 = twice as often (we require 1.5) | §4, everywhere |
| Leverage, conviction | Other strength measures: support minus what independence predicts; how rarely A happens without B | survival features |
| Apriori | Builds candidate itemsets level by level and counts each against the data | §4.2 |
| FP-Growth | Compresses baskets into a tree once and grows itemsets from it; same output as Apriori | §4 (main miner) |
| Pair lift | Lift for "two stocks moved the same way on the same day"; 100 stocks give 4,950 pairs | §5, events §6 |
| Conditional database | Mining only the baskets that contain the left-hand side (how we mine "event → move" rules) | events §5.3 |
| Rolling windows | One rule set per year-long window, moved one month at a time (120 windows) so changes can be dated; this links to change mining and time-series mining (Lecture 12) | §4 |

### Is a pattern real? (Ch. 12 pattern and rule assessment; sampling from Lecture 03)

| Concept | In a few words | Where we use it |
|---|---|---|
| Shuffle (permutation) test | Shuffle each item column separately: each stock keeps how often it moves, links between stocks are destroyed. Rules found there are chance | §4.3 |
| Fisher exact test | For one rule: is the overlap of A and B bigger than if they were independent? (hypergeometric tail) | §4.3, events §5 |
| Multiple testing, Benjamini-Hochberg (FDR) | When you test millions of rules some look significant by luck; BH keeps the expected share of false discoveries at 5%. We count all 7.8 million possible rules, not only the mined ones | §4.3 |
| Bootstrap | Resample the data with replacement many times to get an interval; the *block* bootstrap resamples 10-day blocks to keep bursts together | §5.2, events §5.2 |
| Shift test (calendar permutation) | Slide the whole event calendar by a random number of days (at least 21) and recount, 1,000 times. Keeps the calendar's rhythm, breaks only its link to market days | events §4, §6 |
| p-value | Share of chance runs at least as extreme as the real result | everywhere |
| Mann-Whitney test | Compares two groups by rank (are event days' anomaly scores higher than quiet days'?) | events §5.1 |

### Anomaly detection (Lecture 08)

| Concept | In a few words | Where we use it |
|---|---|---|
| Isolation Forest | Random trees split the days on random stocks; a day isolated after few splits is unusual. Needs no labels | §7 |
| Top 1% | The 27 most unusual days are the "unusual days" | §7, events §4 |
| Jaccard similarity | Overlap of two sets divided by their union. Also a rule measure in Ch. 12 and a cluster-comparison measure in Ch. 17. We use it to compare the Isolation Forest's top days with the days with the most moves: 0.74, so with 100 stocks the forest mostly finds busy days | §7 |

### Classification and evaluation (Lecture 04; Ch. 22 classification assessment, Ch. 24 logistic regression; feature importance from Lecture 06)

| Concept | In a few words | Where we use it |
|---|---|---|
| Target | Does a rule mined today pass the same thresholds again in the next 126 trading days? (yes/no) | §6 |
| Features | Strength (support, confidence, lift, leverage, conviction, Fisher p), scope (sectors spanned, items), history (age, seen in last 12 windows), burstiness, market volatility | §6 |
| Logistic regression, random forest, gradient boosting | A linear model and two tree ensembles | §6 |
| Time split | Train on windows whose future ends before Dec 2022, test on later ones; never a random split, so nothing from the future leaks in | §6 |
| ROC-AUC | Chance the model ranks a surviving rule above a dying one; 0.5 = coin flip | §6 |
| PR-AUC, precision@20% | How good the top of the ranking is; "if we only trusted the top fifth, how many would hold?" | §6 |
| Baselines | Rank by a single number (lift, support, confidence, age); a model is only useful if it beats them | §6 |
| Permutation importance | Shuffle one feature and see how much ROC-AUC drops; the biggest drop is "number of sectors spanned" | §6 |
| Rolling-origin test | Retrain each year on all earlier years and test on that year | §6 |

### Structure change over time (Lecture 12, sequence and time-series mining; change mining)

| Concept | In a few words | Where we use it |
|---|---|---|
| Structure | The whole picture of who moves with whom: all 4,950 pair lifts | events §6 |
| Local break score | 1 − correlation of the pair lifts in the half-year before vs after a date, every week; higher = more change | events §6.1 |
| Break peak | A local maximum above the 90th percentile, at least a quarter apart from the next | events §6.1 |
| Recovery curve | After a shock, similarity of each later half-year to the half-year before, measured in standard deviations from normal drift | events §6.2 |
| Normal drift | Similarity always falls with distance even without events; the same calculation from every month gives the baseline | events §6.2 |
| Temporary / lasting / no break | Rule fixed before running: dip below −1 in the first quarter that returns above −0.5 in year two = temporary; stays at −1 or below = lasting; no dip = no break | events §6.2 |

### Not used (so we can say why if asked)

* **Clustering (Lecture 07, Ch. 13-17):** an earlier version compared hierarchical and spectral clustering of the
  stocks; we dropped it because GICS sectors already give a published grouping and it was not part of the event story.
* **Graph mining, sentiment, topic modelling (Lectures 09-11):** out of scope; news text is listed as future work.

---

## 5. Settings and why

| Setting | Value | Why |
|---|---|---|
| Major move | z ≥ 1 (1 × own 60-day volatility) | Enough moves per window to mine; z = 1.5 tested as a stricter version |
| Beta window | 252 days | One year of history, past only |
| Rolling window, step | 252 baskets, 21 days | One year per rule set, monthly steps → 120 windows |
| Support, confidence, lift, max items | 0.04, 0.4, 1.5, 3 | About 10 days a year, B follows A at least 40% of the time, 50% more than chance |
| Raw/excess/residual comparison | pair rules only | With 100 stocks, raw crash windows would give millions of 3-item rules |
| Unusual days | top 1% (27) | Rare enough to be strange, enough to test |
| Shift test | 1,000 shifts of at least 21 days | A shift of a day or two would still land next to the real event |
| Half-year windows (breaks, recovery) | 126 baskets | Long enough to estimate pair lifts, short enough to date a change; misses breaks lasting only weeks |

---

## 6. What changed when we moved from 40 stocks to the S&P 100

* The stock choice is defensible (S&P's rule, not ours), and there are 11 sectors including 15 financial stocks,
  so "who reacts to the Fed" is a real sector test instead of "one bank reacted".
* Fed result: from "the one bank reacts" to "most sectors are about 1.2× busier on Fed days".
* Recovery: COVID breaks now heal (temporary); DeepSeek no longer leaves a lasting break.
* Prediction got much stronger (ROC-AUC 0.80 vs 0.66), helped by about 130,000 rules instead of 25,000.
* Apriori is now faster than FP-Growth at every rule length we tested (both find identical itemsets).
* Costs: survivorship bias (today's list favours companies that grew), the Isolation Forest mostly finds busy days,
  and with 100 companies many days are earnings days by chance.

---

## 7. Weak spots and how to answer them honestly

* **"Your 33% match comes from events you picked."** Agree; that is why the shocks are reported separately. The
  fair test, scheduled releases, found nothing.
* **"Today's S&P 100 contains the winners."** Agree (survivorship bias). It affects which stocks co-move, hardly the
  event tests, because event dates are fixed in advance. A fully neutral version would let companies enter and leave
  as the index changed; that breaks rolling-window mining and is future work.
* **"Your unusual days are just busy days."** Mostly yes (Jaccard 0.74 with the busiest days). Both say the same:
  the strangest days are when many stocks move on their own.
* **"The temporary/lasting counts change with the settings."** Agree; we call them suggestive and show the
  robustness table.
* **"The prediction does not use events."** Agree; it answers which rules last in general. Testing whether rules
  born near an event die sooner is the next step.
* **"Why lift 1.5 / support 0.04?"** See Section 5. Lower support gives more rules and more chance rules; the
  shuffle test shows chance produces only 0.26% as many rules at our settings.

## 8. Likely oral-exam questions with short answers

1. *Why residual returns and not raw?* Raw rules mostly say "the market moved": 2,461 vs 421 pair rules per window,
   and rule counts track market volatility (0.74 vs 0.42).
2. *Why shift the whole calendar instead of random dates?* It keeps the real rhythm (8 Fed meetings a year, monthly
   releases) and only breaks the link to market days.
3. *What does a lift of 2 mean?* The two stocks make a big same-direction move on the same day twice as often as if
   they were independent.
4. *What if you doubled the data?* Steadier pair lifts and more power in the shift and shuffle tests; small effects
   such as the Fed-day ratios (1.2) would get tighter intervals.
5. *What if you moved the threshold to z = 1.5?* Fewer moves per basket, fewer rules, a noisier break score; Q1 is
   unchanged (33%), the recovery counts change (3 temporary, 3 lasting).
6. *Why Benjamini-Hochberg?* We test millions of possible rules; without a correction many would look significant
   by luck.
7. *Why does ranking by lift fail for durability?* High lift often comes from a few days in one window (bursty
   rules), which do not repeat; old, within-sector rules repeat.

## 9. Where to find things during the exam

| Question about | Open |
|---|---|
| Why the S&P 100, sectors, data checks | `stocks.ipynb` §1-5 |
| Returns, beta, items, baskets | `comovement_rules.ipynb` §3 |
| Rule mining, FP-Growth vs Apriori, chance tests (Q0) | `comovement_rules.ipynb` §4 |
| Sector and semiconductor co-movement | `comovement_rules.ipynb` §5 |
| Rule-survival prediction | `comovement_rules.ipynb` §6 |
| Isolation Forest, unusual days | `comovement_rules.ipynb` §7 |
| Event calendar and why these events | `events.ipynb` §2 |
| Q1 unusual days vs events | `events.ipynb` §4 |
| Q2 who reacts, earnings | `events.ipynb` §5 |
| Q3 breaks and recovery | `events.ipynb` §6 |
| Robustness | `events.ipynb` §7 |
| Every number | `outputs/rules/key_numbers.json`, `outputs/events/key_numbers_events.json` |
