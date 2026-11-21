# Which stock co-movements can you trust? (DSAI4102 final project)

Association rule mining on the daily major moves of 40 US stocks (AI chip makers, Big Tech, traditional software and a non-tech control group), 2016 to November 2026, with the market removed first. We ask:

1. Did ChatGPT's release change how these stocks move together? (placebo break-date test with a control group)
2. Which stocks does the market treat as "AI stocks"? (AI affinity with bootstrap intervals, hierarchical vs spectral clustering)
3. Which mined rules last? (predicting whether a rule is mined again in the next six months)
4. Which days are unusual once the market is removed? (Isolation Forest)

Group: Farid Abdul Rehman (60304642), Muzayyan Parkar (60305825), Mohamad Zain (60306080). Instructor: Moshiur Rahman Farazi.

## How to run

```bash
pip install -r requirements.txt
jupyter notebook final_project.ipynb      # Run All, about 3 minutes
python make_slide_figures.py              # optional: bigger-font figures for the slides
```

The notebook reads `data/prices.csv` and writes every figure and table to `outputs/final/`, including `key_numbers.json`, which holds every number quoted in the slides and the report.

## Files

| File | What it is |
|---|---|
| `final_project.ipynb` | **The final analysis**, top to bottom (sections 1–9) |
| `make_slide_figures.py` | Redraws four figures with larger fonts for the slides (no new analysis) |
| `comovement_association_rules.ipynb` | Step 1: yearly rules on raw returns (kept for reference; superseded) |
| `data/prices.csv` | Adjusted closing prices, 2 Jun 2014 to 13 Nov 2026, 40 stocks + SPY, from Yahoo Finance via `yfinance` (`auto_adjust=True`). Built by the step 1 notebook's `load_prices` |
| `outputs/final/` | All figures (PNG) and tables (CSV) from the final notebook |
| `report/` | IEEE two-column report source (`main.tex`, `refs.bib`, `figures/`). Upload the folder to Overleaf and compile |
| `docs/STUDY_GUIDE.md` | Walkthrough of every concept, function and figure, plus likely oral-exam questions |
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

## Overnight transmission (US AI leaders -> Asian AI supply chain), branch `overnight-transmission`

```bash
pip install -r requirements.txt
python scripts/build_dataset_v2.py      # download (cached in data/raw), clean, align calendars, sanity checks
python -m pytest tests                  # unit tests for the calendar alignment and no-look-ahead rules
```

The dataset script stops with an error if the alignment sanity checks fail (`outputs/v2/sanity.json`).
Data sources, the selection rule for every stock group, and the cleaning steps are in [data/README.md](data/README.md).
