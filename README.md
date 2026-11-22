# Which events change how stocks move together, and do the changes last? (DSAI4102 final project)

Stocks rise and fall together in habits: chip makers move with chip makers, consumer staples with consumer staples.
We mine those habits as association rules on the daily major moves of 40 US stocks (AI chip makers, Big Tech,
traditional software and a non-tech control group), 2016 to November 2026, with the market removed first. Then we
test 368 dated events (Fed rate decisions, CPI and jobs reports, 19 one-off shocks) and company earnings against
chance, and follow the co-movement structure for two years after each shock.

The analysis runs in four steps:

1. **Learn the normal pattern.** Market-model residuals, major moves as items, FP-Growth on 120 rolling one-year
   windows, checked with a shuffle test and Fisher tests with Benjamini–Hochberg (`final_project.ipynb`, sections 3–4).
2. **Find the unusual moments without labels.** Isolation Forest on daily residual z-scores (`final_project.ipynb`,
   section 8) and a weekly structure-break score (`events.ipynb`, section 6).
3. **Match them to events.** Event-date shift test, event-type comparisons, events as items, earnings spillover
   (`events.ipynb`, sections 3–5).
4. **Do the breaks last?** Recovery curves after each shock (`events.ipynb`, section 7).

Supporting results used in the story: the ChatGPT placebo test and AI affinity (`final_project.ipynb`, sections
5–6), and the prediction task, which predicts whether a mined rule is found again in the next six months
(`final_project.ipynb`, section 7). `lag_rules_models_regimes.ipynb` shows why we predict rules and not prices:
next-day price direction is not predictable from these features (ROC-AUC 0.49–0.51).

Group: Farid Abdul Rehman (60304642), Muzayyan Parkar (60305825), Mohamad Zain (60306080). Instructor: Moshiur Rahman Farazi.

## How to run (in this order, from the repo root)

```bash
pip install -r requirements.txt
jupyter nbconvert --to notebook --execute --inplace final_project.ipynb   # about 5 minutes
jupyter nbconvert --to notebook --execute --inplace events.ipynb          # about 30 seconds; needs final_project's outputs
python make_slide_figures.py                                             # a few seconds; needs final_project's outputs
```

Opening each notebook in Jupyter and choosing Run All does the same. The data files are included, so nothing needs
internet access. Optional:

```bash
jupyter nbconvert --to notebook --execute --inplace lag_rules_models_regimes.ipynb   # 10-15 minutes, supporting only
jupyter nbconvert --to notebook --execute --inplace comovement_association_rules.ipynb   # step 1, kept for reference
python build_events.py              # rebuilds data/events.csv (no internet needed)
python build_events.py --earnings   # also re-downloads data/earnings_dates.csv from Yahoo Finance
```

Every notebook writes only to its own output folder, and every number quoted in the slides and the report is
saved in a key-numbers file: `outputs/final/key_numbers.json` and `outputs/events/key_numbers_events.json`.

## Files

| File | What it is |
|---|---|
| `final_project.ipynb` | **Baseline and supporting analyses** (sections 1–9): items, rolling-window rules, chance tests, ChatGPT placebo test, AI affinity and clustering, rule-survival prediction, Isolation Forest. Writes `outputs/final/` |
| `events.ipynb` | **The event analysis** (sections 1–9): which events line up with unusual days and structure breaks, who reacts to rate news, earnings spillover, and whether breaks last. Writes `outputs/events/`. Details in [EVENTS.md](EVENTS.md) |
| `build_events.py` | Builds `data/events.csv` (FOMC, CPI, jobs reports, shocks, each with a source link) and, with `--earnings`, `data/earnings_dates.csv` |
| `make_slide_figures.py` | Redraws four `final_project` figures with large fonts (`outputs/final/slides/`) and refreshes `report/figures/`. It does not build a PowerPoint |
| `lag_rules_models_regimes.ipynb` | Supporting: next-day rules, price-direction prediction (fails, ROC-AUC about 0.50) and market regimes. Writes `outputs/lag/` |
| `comovement_association_rules.ipynb` | Step 1: yearly rules on raw returns (kept for reference; superseded). Writes `outputs/step1/` |
| `data/prices.csv` | Adjusted closing prices, 2 Jun 2014 to 13 Nov 2026, 40 stocks + SPY, from Yahoo Finance via `yfinance` (`auto_adjust=True`). Built by the step 1 notebook's `load_prices` |
| `data/events.csv`, `data/earnings_dates.csv` | Event calendar and earnings dates used by `events.ipynb` |
| `outputs/final/`, `outputs/events/`, `outputs/lag/`, `outputs/step1/` | Figures (PNG) and tables (CSV) from each notebook |
| `report/` | IEEE two-column report source (`main.tex`, `refs.bib`, `figures/`). Upload the folder to Overleaf and compile |
| `docs/reading_list.md` | Background reading and papers |

## Main settings

| Setting | Value | Meaning |
|---|---|---|
| `MAIN_MODE` | `residual` | return minus beta × SPY return (beta from the previous 252 days) |
| `Z_K`, `VOL_WINDOW` | 1.0, 60 | a major move is at least 1 × the stock's own 60-day residual volatility |
| `WINDOW`, `STEP` | 252, 21 | one-year rolling windows moved one month at a time (120 windows) |
| `MIN_SUPPORT`, `MIN_CONFIDENCE`, `MIN_LIFT`, `MAX_LEN` | 0.04, 0.4, 1.5, 3 | mining thresholds |
| `TOP_SHARE` | 0.01 | an "unusual day" is in the top 1% of Isolation Forest scores (27 days) |
| `N_SHIFTS`, `MIN_SHIFT` | 1,000, 21 | random calendar shifts of at least a month for the event-date test |
| `SPAN` | 126 | half-year windows before and after a date for the break score and recovery curves |
| `CHATGPT_DATE` | 2022-12-01 | first trading day after ChatGPT's release |
| `FUTURE_DAYS` | 126 | a rule "survives" if it is mined again from the next 126 baskets |

## Data sources

Prices: Yahoo Finance through the open-source [`yfinance`](https://github.com/ranaroussi/yfinance) library, downloaded
once and saved to `data/prices.csv` so everyone works from the same data. Event dates: Federal Reserve and BLS
calendars, plus a source link for every one-off shock (see `EVENTS.md`). Earnings dates: Yahoo Finance via `yfinance`.

## Acknowledgement

The code and drafts in this repository were written with the help of an AI assistant (Claude, Anthropic) and reviewed by the group.

## Other branches

* `overnight-transmission`: does AI news travel overnight from the US to Japan, Taiwan and Korea? (lagged rules, trading test, prediction)
* `final-project`, `event-analysis`, `lag-baseline`: the earlier lines of work, all contained in `main`
* tag `archive/main-2026-11-22`: `main` exactly as it was before the event analysis became `main`
