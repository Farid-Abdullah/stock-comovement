# Which events change how stocks move together, and do the changes last? (DSAI4102 final project)

Stocks move together in habits: chip makers with chip makers, banks with banks. We mine those habits as
**association rules** on the daily major moves of the **S&P 100** (100 companies, 11 sectors), January 2016 to
13 November 2026, after removing the market from every return. We then test **368 dated events** (Federal Reserve
rate decisions, inflation and jobs reports, 19 one-off shocks) and **company earnings** against chance, and follow
the co-movement structure for two years after each shock.

Questions:

* **Q0** Are the mined rules real co-movement, or just the market moving? (`comovement_rules.ipynb`)
* **Q1** Do events explain the strangest days? (`events.ipynb`, Section 4)
* **Q2** Who reacts to scheduled news, and to company earnings? (`events.ipynb`, Section 5)
* **Q3** When events change co-movement, does the change last? (`events.ipynb`, Section 6)
* **Prediction** Which mined rules last? (`comovement_rules.ipynb`, Section 6)

Group: Farid Abdul Rehman (60304642), Muzayyan Parkar (60305825), Mohamad Zain (60306080). Instructor: Moshiur Rahman Farazi.

## How to run

From the repo root, run the three notebooks **in this order** (Run All in Jupyter, or the commands below). The
first run needs internet access to Yahoo Finance; later runs read the saved files in `data/`.

```bash
pip install -r requirements.txt
jupyter nbconvert --to notebook --execute --inplace stocks.ipynb             # 1. about 1-2 minutes (price download)
jupyter nbconvert --to notebook --execute --inplace comovement_rules.ipynb   # 2. about 10-30 minutes
jupyter nbconvert --to notebook --execute --inplace events.ipynb             # 3. about 5 minutes (earnings download)
```

Each notebook reads only files written by the notebooks before it, and writes only to its own output folder.
To start completely fresh, delete `data/` and `outputs/` and run all three again.

## What each notebook does and produces

| # | Notebook | What it does | Reads | Writes |
|---|---|---|---|---|
| 1 | `stocks.ipynb` | Explains what the S&P 100 is and why we use it (a list chosen by S&P with a published rule, not by us), lists the 100 companies with their GICS sectors, downloads adjusted daily prices, checks the data (gaps, late listings, extreme moves) and explores how the sectors performed | internet (Yahoo Finance) | `data/prices.csv`, `data/stocks.csv`, `outputs/stocks/` |
| 2 | `comovement_rules.ipynb` | Removes the market from every return (market model), turns each day into a basket of major moves, mines rules with FP-Growth on 120 rolling one-year windows, compares raw / excess / residual returns, tests the rules against shuffled data and with Fisher tests, tracks co-movement inside and between sectors and with the semiconductor stocks, predicts which rules last, and finds the unusual days with an Isolation Forest | `data/prices.csv`, `data/stocks.csv` | `outputs/rules/` (figures, tables, `key_numbers.json`) |
| 3 | `events.ipynb` | Builds the event calendar and explains why each kind of event is in the test, downloads earnings dates, then answers Q1-Q3: unusual days vs a shifted calendar, which sectors react on Fed / CPI / jobs days, earnings spillover, structure breaks and recovery curves, plus a robustness check | `data/prices.csv`, `data/stocks.csv`, `outputs/rules/top_anomalous_days.csv`, internet (Yahoo Finance, earnings) | `data/events.csv`, `data/earnings_dates.csv`, `outputs/events/` (figures, tables, `key_numbers_events.json`) |

Every number quoted in the slides is in `outputs/rules/key_numbers.json` or `outputs/events/key_numbers_events.json`.

## Main outputs

| File | What it shows |
|---|---|
| `outputs/stocks/3_1_companies_per_sector.png` | S&P 100 companies per sector |
| `outputs/stocks/6_2_sector_returns_by_year.png` | Each sector's cumulative return, year by year, with SPY |
| `outputs/rules/4_1_rules_per_window_by_mode.png` | Rules per window under raw, excess and residual returns (Q0) |
| `outputs/rules/4_3_chance_test.png` | Real rules, significant rules and rules found in shuffled data (Q0) |
| `outputs/rules/5_1_structure_over_time.png` | Mean pair lift inside sectors, between sectors and around the semiconductor stocks |
| `outputs/rules/5_2_semi_affinity_change.png` | Stocks whose co-movement with the semiconductor stocks changed beyond noise |
| `outputs/rules/6_2_survival_models.png` | Rule-survival models against one-feature baselines |
| `outputs/rules/7_1_anomaly_timeline.png` | Isolation Forest anomaly score per day; the top 1% are the unusual days |
| `outputs/events/3_1_events_on_spy.png` | The S&P 500 (SPY) with the one-off shocks and scheduled releases marked |
| `outputs/events/4_1_unusual_days_shift_test.png` | Unusual days matched to events, real vs 1,000 shifted calendars (Q1) |
| `outputs/events/top_unusual_days_labelled.csv` | The 27 unusual days with their events and a category |
| `outputs/events/5_2_move_ratio_by_sector.png` | Which sectors move more than usual on Fed, CPI and jobs days (Q2) |
| `outputs/events/5_4_earnings_spillover.png` | How much an earnings move pulls the company's own sector (Q2) |
| `outputs/events/6_1_local_breaks_and_shocks.png` | Weekly structure-break score with the shocks (Q3) |
| `outputs/events/6_3_recovery_curves_four_events.png` | Recovery curves for four shocks (Q3) |

## Folders

| Folder | Contents |
|---|---|
| `data/` | Inputs built by the notebooks: prices, the company list, the event calendar, earnings dates |
| `outputs/stocks/`, `outputs/rules/`, `outputs/events/` | Figures (PNG), tables (CSV) and key numbers (JSON) of each notebook |
| `docs/` | `reading_list.md` (background reading) |
| `report/` | Report source (IEEE two-column LaTeX); still describes the earlier 40-stock version and will be updated |
| `DETAILS.md` | Our own notes: the story, the concepts and how they map to the course |

## Data sources

* **Prices and earnings dates:** Yahoo Finance through the open-source [`yfinance`](https://github.com/ranaroussi/yfinance) library (adjusted closes, `auto_adjust=True`).
* **S&P 100 constituents and sectors:** [Wikipedia, S&P 100](https://en.wikipedia.org/wiki/S%26P_100), read on 22 Nov 2026; index description from [S&P Dow Jones Indices](https://www.spglobal.com/spdji/en/indices/equity/sp-100).
* **Fed decisions:** [Federal Reserve meeting calendars](https://www.federalreserve.gov/monetarypolicy/fomccalendars.htm). **CPI and jobs reports:** BLS release archives ([CPI](https://www.bls.gov/bls/news-release/cpi.htm), [Employment Situation](https://www.bls.gov/bls/news-release/empsit.htm)).
* **One-off shocks:** each row of `data/events.csv` links a news report or official release confirming the date.

## Acknowledgement

The code and drafts in this repository were written with the help of an AI assistant (Claude, Anthropic) and reviewed by the group.

## Other branches and tags

* tag `presentation-40-stocks`: the earlier version with 40 hand-picked stocks in four groups.
* `final-project`, `event-analysis`, `lag-baseline`, `overnight-transmission`: earlier lines of work.
