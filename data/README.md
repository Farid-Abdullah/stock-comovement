# Data for the overnight-transmission study

* **Source:** Yahoo Finance via `yfinance` 1.8.0, daily bars, `auto_adjust=True` (prices adjusted for splits
  and dividends), fields Open, Close, Volume.
* **Downloaded:** 2026-11-21 by `scripts/build_dataset_v2.py` (rerun it to rebuild every file here; `--refresh` downloads
  again). Period: 2015-01-01 to 2026-11-20.
* **Dates** are each exchange's local trading date (as Yahoo reports daily bars).

## Files

| file | content |
|---|---|
| `raw/<ticker>.csv` | as downloaded (indices: `^N225` -> `IDX_N225.csv`) |
| `prices_v2.csv`, `prices_v2.parquet` | cleaned long table: date, ticker, open, close, volume |
| `universe.csv` | ticker, market, group, home index, company name, approximate index weight |
| `calendar_v2.csv` | for each US date t and Asian market: follower date (first local trading date after t), gap in days |
| `download_log.json` | failed, dropped and late-listed tickers; cleaning counts per ticker |
| `prices.csv` | the earlier 40-stock US file used by `final_project.ipynb` and `lag_rules_models_regimes.ipynb` |

## Which stocks, and why (selection rule per group)

| group | rule | tickers |
|---|---|---|
| US AI leaders | US companies whose news drives the AI trade: the main AI chip designers (Nvidia, AMD, Broadcom, Micron) and the hyperscalers that buy AI hardware (Microsoft, Alphabet, Meta, Amazon, Oracle). Large, liquid, listed for the whole period. | NVDA, AMD, AVGO, MU, MSFT, GOOGL, META, AMZN, ORCL |
| US AI infrastructure | Smaller US firms that supply AI data centres (servers, power, cooling, networking, optics). Same time zone as the leaders, so they test a size effect without the overnight gap. | SMCI, VRT, ANET, MRVL, COHR, CLS, VST, DELL |
| US non-AI controls | Large US firms with no AI exposure (banks, energy, consumer staples, healthcare). They test whether any transmission is just "the US market moved". | JPM, XOM, PG, KO, WMT, JNJ |
| Asian AI followers | Asian companies in the AI hardware supply chain: TSMC and ASE (chip making and packaging), Foxconn, Quanta, Wistron, Wiwynn (AI servers), Delta (power), MediaTek (chips), Samsung, SK hynix (memory, HBM), Hanmi (HBM equipment), Tokyo Electron, Advantest, Disco, Lasertec (chip equipment), SoftBank (AI investor, owns Arm). | 2330.TW, 2317.TW, 2382.TW, 3231.TW, 6669.TW, 2308.TW, 2454.TW, 3711.TW, 005930.KS, 000660.KS, 042700.KS, 8035.T, 6857.T, 6146.T, 6920.T, 9984.T |
| Asian non-AI controls | Large, liquid stocks in the same three markets without AI exposure (cars, banks, pharma, telecom, insurance). Same markets and hours as the AI followers, so they share every calendar and market effect. | 7203.T, 8306.T, 4502.T, 005380.KS, 2412.TW, 2882.TW |
| Benchmarks | SPY (US market), ^N225, ^KS11, ^TWII (home indices for Japan, Korea, Taiwan), ^VIX (US volatility), SMH (semiconductor ETF). | SPY, ^N225, ^KS11, ^TWII, ^VIX, SMH |

## Cleaning (all counts in `download_log.json`)

* Each market's calendar = the dates of its home index, plus any day on which more than half of that market's stocks
  really traded (Yahoo occasionally misses an index row).
* Yahoo adds rows on some holidays (and a few data gaps) that repeat the previous close with zero volume. Rows with
  zero volume and an unchanged close are treated as missing; rows outside the market calendar are dropped.
* Tickers that fail to download or have fewer than 3 years of data are dropped and logged, never replaced.
* Late listings are kept (logged): they enter the analysis once they have enough history.

## Calendar alignment

US close (16:00 New York) is before the next Asian open. For every US trading date t, the **follower date** of an
Asian market is that market's first trading date strictly after t. Pairs with a gap of more than 4 calendar
days (long Asian holidays) are dropped. If several US dates map to the same follower date (Asia closed while the US
traded), only the latest US date is kept. Code: `src/overnight_data.py::align_calendars`, tests:
`tests/test_alignment.py`, sanity checks: `outputs/v2/sanity.json`.

## Index weights (robustness check only)

`universe.csv` has an approximate weight w of each Asian stock in its home index, used only for the ex-stock index
r_ex = (r_index - w * r_stock) / (1 - w). The weights are rounded author estimates of typical 2020-2025 weights from
index-provider factsheets (TWSE for ^TWII, KRX for ^KS11, Nikkei for the price-weighted ^N225) and are held constant
over the sample, although real weights drift (TSMC's share of ^TWII rose from about 30% to over 40%). They are
approximate and should be checked against the factsheets before being quoted. ^TOPX (TOPIX) is not available on
Yahoo Finance, so Japan uses ^N225 ex-stock.

## Trading-cost assumptions (code: `src/costs.py`)

All trades in the notebook are intraday round trips: in at the Asian open, out at the close of the same session.
Cost per round trip = securities transaction tax on the sale + assumed fees and half-spreads.

| market | tax on the sale | fees + spread (assumed) | round trip |
|---|---|---|---|
| Japan | none | 10 bps | 10 bps |
| Taiwan | 0.30% until 27 Apr 2017; 0.15% day-trade rate (same-session buy and sell) from 28 Apr 2017 | 5 bps | 35 bps, then 20 bps |
| Korea (KOSPI) | securities transaction tax + 0.15% special tax for rural development: 0.30% until 29 May 2019, 0.25% from 30 May 2019, 0.23% 2021-2022, 0.20% 2023 (*), 0.18% 2024, 0.15% 2025, 0.20% from 2026 | 5 bps | 23-35 bps by year |

The rate in force on the trade date is used. Sources:
* Korea: EY Tax News, "Korea proposes reduced securities transaction tax rates" (18 Apr 2019,
  https://taxnews.ey.com/news/2019-0797); Asia Economy, "Securities transaction tax cut... KOSPI 0.1% -> 0.08%"
  (28 Dec 2020, https://www.asiae.co.kr/en/article/2020122807581924586); PwC Worldwide Tax Summaries, Korea, other
  taxes (0.18% in 2024, 0.15% in 2025, 0.20% from 2026 including the rural tax,
  https://taxsummaries.pwc.com/Republic-of-Korea/Corporate/Other-taxes); Asia Economy, "Securities transaction tax
  to rise from January" (1 Dec 2025, https://asiae.co.kr/en/article/2025120109040485489).
  (*) The 2023 rate of 0.20% (0.05% + 0.15%) could not be confirmed against a source and should be checked.
* Taiwan: Taipei Times / Focus Taiwan on the day-trading tax cut (0.15% instead of 0.30% from 28 Apr 2017,
  extended in 2018, 2021 and in Dec 2024 to 2027): https://focustaiwan.tw/business/202412310013,
  https://www.taipeitimes.com/News/taiwan/archives/2021/12/22/2003770006
* Japan: no securities transaction tax; 10 bps for fees and spread is our assumption for large, liquid stocks.
