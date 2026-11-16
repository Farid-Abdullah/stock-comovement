# Stock co-movement by year: association rule mining (DSAI4102 project, step 1)

Mines association rules on the daily major moves of 40 stocks, separately for each year from 2015 to 2026, and compares the yearly rule sets.

- **Basket** = one trading day. **Item** = a stock that made a major move that day, with its direction (`NVDA_UP`, `IBM_DOWN`).
- **One rule set per year** (about 250 baskets each), mined with FP-Growth and checked against Apriori.

## How to run

```bash
pip install -r requirements.txt
jupyter notebook comovement_association_rules.ipynb
```

Then choose *Run All*. The first run downloads prices from Yahoo Finance and saves them to `data/prices.csv`. Later runs read that file, so everyone in the group works from the same data. Delete the file to download again.

## Files

| File | What it is |
|---|---|
| `comovement_association_rules.ipynb` | The whole analysis, top to bottom |
| `requirements.txt` | Python packages needed |
| `data/prices.csv` | Created on first run: adjusted closing prices (submit this with the report) |
| `outputs/` | Created on each run: every figure as PNG and every table as CSV |

## Settings (first code cell of the notebook)

| Setting | Default | Meaning |
|---|---|---|
| `GROUPS` | 40 tickers in 4 groups | Which stocks, and which group each belongs to |
| `RETURN_MODE` | `"raw"` | `"excess"` subtracts the S&P 500 return first, so market-wide days stop counting as co-movement |
| `MOVE_METHOD`, `Z_K` | `"zscore"`, `1.0` | A move is major when it is at least `Z_K` times the stock's own 60-day volatility. `"fixed"` uses a flat ±2% instead |
| `MIN_SUPPORT`, `MIN_CONFIDENCE`, `MIN_LIFT`, `MAX_LEN` | 0.05, 0.5, 1.5, 3 | Mining thresholds |
| `SPLIT_YEAR` | 2023 | Year used to label rules as stable, emerged or disappeared |

## Reading list

See [docs/reading_list.md](docs/reading_list.md). It has finance basics for beginners, an AI timeline, the market events behind each year's results, and academic papers for the Related Work section.


## Acknowledgement

The code in this folder was created with an AI assistant (Claude, Anthropic).
