# Which stock co-movements can you trust? (DSAI4102 final project)

Association rule mining on the daily major moves of 40 US stocks (AI chip makers, Big Tech, traditional software and a non-tech control group), 2016 to November 2026, with the market removed first. We ask:

1. Did ChatGPT's release change how these stocks move together? (placebo break-date test with a control group)
2. Which stocks does the market treat as "AI stocks"? (AI affinity with bootstrap intervals, hierarchical vs spectral clustering)
3. Which mined rules last? (predicting whether a rule is mined again in the next six months)
4. Which days are unusual once the market is removed? (Isolation Forest)
5. Which events (rate decisions, CPI and jobs reports, earnings, one-off shocks) line up with the unusual days and structure breaks, and do the breaks last? (`events.ipynb`, see [EVENTS.md](EVENTS.md))

Group: Farid Abdul Rehman (60304642), Muzayyan Parkar (60305825), Mohamad Zain (60306080). Instructor: Moshiur Rahman Farazi.

## How to run

```bash
pip install -r requirements.txt
jupyter notebook final_project.ipynb      # Run All, about 3 minutes
jupyter notebook events.ipynb             # Run All after final_project, about 30 seconds
```

`final_project.ipynb` reads `data/prices.csv` and writes every figure and table to `outputs/final/`, including `key_numbers.json`, which holds every number quoted in the slides and the report. `events.ipynb` also reads `data/events.csv`, `data/earnings_dates.csv` and two tables from `outputs/final/`, and writes to `outputs/events/` (numbers in `key_numbers_events.json`). Each notebook writes only to its own folder.

## Files

| File | What it is |
|---|---|
| `final_project.ipynb` | **The final analysis**, top to bottom (sections 1–9) |
| `events.ipynb` | **The event layer**: which events break co-movement and whether the breaks last (sections 1–9; details in `EVENTS.md`) |
| `build_events.py` | Builds `data/events.csv` (FOMC, CPI, jobs reports, shocks) and, with `--earnings`, `data/earnings_dates.csv` |
| `data/events.csv`, `data/earnings_dates.csv` | Event calendar and earnings dates used by `events.ipynb` |
| `comovement_association_rules.ipynb` | Step 1: yearly rules on raw returns (kept for reference; superseded). Writes to `outputs/step1/` |
| `data/prices.csv` | Adjusted closing prices, 2 Jun 2014 to 13 Nov 2026, 40 stocks + SPY, from Yahoo Finance via `yfinance` (`auto_adjust=True`). Built by the step 1 notebook's `load_prices` |
| `outputs/final/` | All figures (PNG) and tables (CSV) from the final notebook (`slides/` holds larger-font copies of four figures) |
| `outputs/events/` | All figures and tables from the event notebook |
| `outputs/step1/` | Figures and tables from the step 1 notebook |
| `report/` | IEEE two-column report source (`main.tex`, `refs.bib`, `figures/`). Upload the folder to Overleaf and compile |
| `docs/reading_list.md` | Background reading and papers |

## Main settings (first code cell)

| Setting | Value | Meaning |
|---|---|---|
| `MAIN_MODE` | `residual` | return minus beta × SPY return (beta from the previous 252 days) |
| `Z_K`, `VOL_WINDOW` | 1.0, 60 | a major move is at least 1 × the stock's own 60-day residual volatility |
| `WINDOW`, `STEP` | 252, 21 | one-year rolling windows moved one month at a time (120 windows) |
| `MIN_SUPPORT`, `MIN_CONFIDENCE`, `MIN_LIFT`, `MAX_LEN` | 0.04, 0.4, 1.5, 3 | mining thresholds |
| `CHATGPT_DATE` | 2022-12-01 | first trading day after ChatGPT's release |
| `FUTURE_DAYS` | 126 | a rule "survives" if it is mined again from the next 126 baskets |

## Data source

Prices: Yahoo Finance through the open-source [`yfinance`](https://github.com/ranaroussi/yfinance) library, downloaded once and saved to `data/prices.csv` so everyone works from the same data. To rebuild it, delete the file and run the step 1 notebook's data cell.

## Acknowledgement

The code and drafts in this repository were written with the help of an AI assistant (Claude, Anthropic) and reviewed by the group.

## Other branches

* `overnight-transmission`: does AI news travel overnight from the US to Japan, Taiwan and Korea? (lagged rules, trading test, prediction)
* `lag-baseline`: the lag-rules, models and regimes notebook (`lag_rules_models_regimes.ipynb`, `outputs/lag/`)
* tag `archive/main-2026-11-22`: `main` exactly as it was before the event layer became `main`
