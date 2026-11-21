"""Build the dataset for overnight_transmission.ipynb: download, clean, align calendars, sanity-check.

Run from the repo root:
    python scripts/build_dataset_v2.py            # reuses data/raw/*.csv if they exist
    python scripts/build_dataset_v2.py --refresh  # downloads everything again

Writes
    data/raw/<ticker>.csv        one file per ticker as downloaded (Open, Close, Volume; adjusted)
    data/prices_v2.csv/.parquet  tidy long table: date, ticker, open, close, volume (after cleaning)
    data/universe.csv            ticker, market, group, home index, name, index weight
    data/calendar_v2.csv         for each US date t and Asian market: the follower date and the gap in days
    data/download_log.json       failed / dropped / late-listed tickers, cleaning counts
    outputs/v2/sanity.json       the alignment sanity checks (the script stops if they fail)

The analysis notebook never downloads; it reads these files.
"""
import argparse
import json
import sys
import time
from datetime import date
from pathlib import Path

import numpy as np
import pandas as pd
import yfinance as yf

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.universe import ALL_TICKERS, HOME_INDEX, universe_rows          # noqa: E402

STOCK_MARKET = {r["ticker"]: r["market"] for r in universe_rows() if r["group"] != "Benchmark"}
from src.overnight_data import (align_calendars, wide, local_returns,    # noqa: E402
                                follower_frame)

START = "2015-01-01"
MIN_YEARS = 3                    # a ticker with fewer trading days than 3 x 252 is dropped (and logged)
BATCH_SIZE = 6                   # Yahoo rate-limits large requests; small batches + a pause are reliable
PAUSE_SECONDS = 2.0
RETRIES = 3
MAX_GAP_DAYS = 4                 # follower date more than 4 calendar days after the US date = holiday gap, dropped

DATA = ROOT / "data"
RAW = DATA / "raw"
OUT = ROOT / "outputs" / "v2"


def raw_path(ticker):
    # '^N225' -> 'IDX_N225.csv' so file names stay portable
    return RAW / (ticker.replace("^", "IDX_") + ".csv")


def download_batch(tickers, end):
    # One yfinance request for a few tickers; returns {ticker: DataFrame(Open, Close, Volume)}.
    data = yf.download(tickers, start=START, end=end, auto_adjust=True, group_by="ticker",
                       progress=False, threads=False)
    out = {}
    for t in tickers:
        if t not in data.columns.get_level_values(0):
            continue
        df = data[t][["Open", "Close", "Volume"]].dropna(subset=["Close"])
        if len(df):
            df.index = pd.to_datetime(df.index).tz_localize(None).normalize()   # local exchange trading date
            out[t] = df
    return out


def download_all(tickers, refresh):
    # Download in small batches with retries; tickers already on disk are reused unless refresh=True.
    RAW.mkdir(parents=True, exist_ok=True)
    end = (pd.Timestamp.today() + pd.Timedelta(days=1)).strftime("%Y-%m-%d")    # yfinance's end is exclusive
    todo = [t for t in tickers if refresh or not raw_path(t).exists()]
    failed = []
    for i in range(0, len(todo), BATCH_SIZE):
        batch = todo[i:i + BATCH_SIZE]
        for attempt in range(1, RETRIES + 1):
            got = download_batch(batch, end)
            for t, df in got.items():
                df.to_csv(raw_path(t), index_label="Date")
            batch = [t for t in batch if t not in got]
            if not batch:
                break
            print(f"  retry {attempt}/{RETRIES} for {batch}")
            time.sleep(PAUSE_SECONDS * 2 * attempt)
        failed += batch
        print(f"  downloaded {min(i + BATCH_SIZE, len(todo))}/{len(todo)}")
        time.sleep(PAUSE_SECONDS)
    return failed


def load_raw(tickers):
    frames = {}
    for t in tickers:
        if raw_path(t).exists():
            frames[t] = pd.read_csv(raw_path(t), index_col="Date", parse_dates=True)
    return frames


# ---- cleaning --------------------------------------------------------------------------------------------------

def is_stale(df):
    # Yahoo fills some holidays and data gaps with a copy of the previous close and zero volume: not a real trade.
    return (df["Volume"] == 0) & (df["Close"] == df["Close"].shift(1))


def market_calendar(raw, universe, market):
    """Trading dates of one market: its home index's dates, plus days on which most of its stocks really traded.

    The index alone is not enough because Yahoo occasionally misses an index row; stock rows alone are not enough
    because Yahoo adds stale rows on holidays. Index volume is unreliable on Yahoo, so it is not used.
    """
    index = raw[HOME_INDEX[market]]
    index_days = index.index[index["Close"] != index["Close"].shift(1)]
    stocks = universe[(universe["market"] == market) & (universe["group"] != "Benchmark")].index
    traded = pd.DataFrame({t: ~is_stale(raw[t]) & (raw[t]["Volume"] > 0) for t in stocks if t in raw})
    busy_days = traded.index[traded.mean(axis=1) > 0.5]
    return index_days.union(busy_days)


def clean(raw, universe):
    """Keep each ticker's rows on its market's calendar only; stale rows become missing. Returns long table + log."""
    calendars = {m: market_calendar(raw, universe, m) for m in HOME_INDEX}
    rows, log = [], {}
    for t, df in raw.items():
        market = universe.loc[t, "market"]
        cal = calendars[market]
        off_calendar = int((~df.index.isin(cal)).sum())
        df = df.reindex(cal)                                   # dates the market traded; missing ones become NaN
        stale = is_stale(df) if universe.loc[t, "group"] != "Benchmark" else pd.Series(False, index=df.index)
        df.loc[stale, ["Open", "Close"]] = np.nan
        first = df["Close"].first_valid_index()
        df = df.loc[first:]
        log[t] = {"rows_off_calendar_dropped": off_calendar, "stale_rows_set_missing": int(stale.sum()),
                  "missing_days_after_listing": int(df["Close"].isna().sum()),
                  "first_date": str(first.date()), "trading_days": int(df["Close"].notna().sum())}
        rows.append(pd.DataFrame({"date": df.index, "ticker": t, "open": df["Open"].to_numpy(),
                                  "close": df["Close"].to_numpy(), "volume": df["Volume"].to_numpy()}))
    return pd.concat(rows, ignore_index=True), calendars, log


# ---- sanity checks ---------------------------------------------------------------------------------------------

def oc_checks(corr_oc, corr_cc):
    # Both versions of check 2 are recorded. The abs version was the first draft; it was dropped because it fails
    # when oc is clearly NEGATIVE (a partial reversal of the opening gap), which is not a sign of misalignment.
    return {"signed_used": bool(corr_oc < 0.5 * corr_cc), "abs_dropped": bool(abs(corr_oc) < 0.5 * corr_cc)}


def sanity_checks(prices, calendars):
    """If the calendar alignment is right, SPY on US date t must predict the Asian index on the follower date.

    Three checks per Asian market (all must hold, otherwise the script stops):
      1. corr(SPY_t, index close-to-close on the follower date) is clearly positive (> 0.2);
      2. with open-to-close returns the correlation is much smaller (< half of check 1): the reaction happens at
         the Asian open, so little is left after it. The check is signed on purpose: a NEGATIVE oc correlation
         (part of the opening move reverses during the day) is a finding, not an alignment error; a wrong
         alignment would give oc close to 0 AND a small cc;
      3. corr(SPY_t, index on the SAME calendar date t, a session that ended before the US opened) is smaller than
         check 1. If the dates were shifted by a day, check 3 would be the large one.
    """
    close, open_ = wide(prices, "close"), wide(prices, "open")
    spy = local_returns(close, open_, ["SPY"], calendars["US"])[0]["SPY"]
    results, problems = {}, []
    for market in ["JP", "KR", "TW"]:
        idx = HOME_INDEX[market]
        cc, oc, _ = (r[idx] for r in local_returns(close, open_, [idx], calendars[market]))
        pairs, counts = align_calendars(calendars["US"], calendars[market], MAX_GAP_DAYS)   # same pairs as saved
        f_cc = follower_frame(cc.to_frame(), pairs)[idx]
        f_oc = follower_frame(oc.to_frame(), pairs)[idx]
        same_day = cc.reindex(spy.index)                       # Asian session on calendar date t (before the US)
        r = {"corr_follower_cc": spy.corr(f_cc), "corr_follower_oc": spy.corr(f_oc),
             "corr_same_calendar_day_cc": spy.corr(same_day), "pairs": counts}
        results[idx] = {k: (round(float(v), 4) if not isinstance(v, dict) else v) for k, v in r.items()}
        results[idx]["oc_check"] = oc_checks(r["corr_follower_oc"], r["corr_follower_cc"])
        if not r["corr_follower_cc"] > 0.2:
            problems.append(f"{idx}: follower cc correlation {r['corr_follower_cc']:.3f} is not clearly positive")
        if not r["corr_follower_oc"] < 0.5 * r["corr_follower_cc"]:
            problems.append(f"{idx}: oc correlation {r['corr_follower_oc']:.3f} not much smaller than cc")
        if not r["corr_same_calendar_day_cc"] < r["corr_follower_cc"]:
            problems.append(f"{idx}: same-day correlation {r['corr_same_calendar_day_cc']:.3f} >= follower")

        # 4. the same at stock level (mean over the market's stocks). Index opens can be stale (an index's 09:00
        #    value uses previous closes of stocks that have not traded yet), so the stock-level oc check is the one
        #    that matters for the tradeable oc returns. The overnight gap (previous close -> open) should carry
        #    most of the reaction.
        stocks = [t for t in close.columns if t in STOCK_MARKET and STOCK_MARKET[t] == market]
        s_cc, s_oc, s_gap = (follower_frame(r, pairs)
                             for r in local_returns(close, open_, stocks, calendars[market]))
        spy_t = spy.reindex(s_cc.index)
        stock = {"mean_corr_cc": s_cc.corrwith(spy_t).mean(), "mean_corr_oc": s_oc.corrwith(spy_t).mean(),
                 "mean_corr_overnight_gap": s_gap.corrwith(spy_t).mean(), "n_stocks": len(stocks)}
        results[idx]["stocks"] = {k: round(float(v), 4) for k, v in stock.items()}
        results[idx]["stocks"]["oc_check"] = oc_checks(stock["mean_corr_oc"], stock["mean_corr_cc"])
        if not stock["mean_corr_oc"] < 0.5 * stock["mean_corr_cc"]:
            problems.append(f"{market} stocks: oc correlation {stock['mean_corr_oc']:.3f} not much smaller than cc")
    return results, problems


# ---- documentation ---------------------------------------------------------------------------------------------

README = """# Data for the overnight-transmission study

* **Source:** Yahoo Finance via `yfinance` {yf_version}, daily bars, `auto_adjust=True` (prices adjusted for splits
  and dividends), fields Open, Close, Volume.
* **Downloaded:** {today} by `scripts/build_dataset_v2.py` (rerun it to rebuild every file here; `--refresh` downloads
  again). Period: {start} to {last}.
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
| US AI leaders | US companies whose news drives the AI trade: the main AI chip designers (Nvidia, AMD, Broadcom, Micron) and the hyperscalers that buy AI hardware (Microsoft, Alphabet, Meta, Amazon, Oracle). Large, liquid, listed for the whole period. | {g_leaders} |
| US AI infrastructure | Smaller US firms that supply AI data centres (servers, power, cooling, networking, optics). Same time zone as the leaders, so they test a size effect without the overnight gap. | {g_infra} |
| US non-AI controls | Large US firms with no AI exposure (banks, energy, consumer staples, healthcare). They test whether any transmission is just "the US market moved". | {g_us_ctrl} |
| Asian AI followers | Asian companies in the AI hardware supply chain: TSMC and ASE (chip making and packaging), Foxconn, Quanta, Wistron, Wiwynn (AI servers), Delta (power), MediaTek (chips), Samsung, SK hynix (memory, HBM), Hanmi (HBM equipment), Tokyo Electron, Advantest, Disco, Lasertec (chip equipment), SoftBank (AI investor, owns Arm). | {g_asia_ai} |
| Asian non-AI controls | Large, liquid stocks in the same three markets without AI exposure (cars, banks, pharma, telecom, insurance). Same markets and hours as the AI followers, so they share every calendar and market effect. | {g_asia_ctrl} |
| Benchmarks | SPY (US market), ^N225, ^KS11, ^TWII (home indices for Japan, Korea, Taiwan), ^VIX (US volatility), SMH (semiconductor ETF). | {g_bench} |

## Cleaning (all counts in `download_log.json`)

* Each market's calendar = the dates of its home index, plus any day on which more than half of that market's stocks
  really traded (Yahoo occasionally misses an index row).
* Yahoo adds rows on some holidays (and a few data gaps) that repeat the previous close with zero volume. Rows with
  zero volume and an unchanged close are treated as missing; rows outside the market calendar are dropped.
* Tickers that fail to download or have fewer than {min_years} years of data are dropped and logged, never replaced.
* Late listings are kept (logged): they enter the analysis once they have enough history.

## Calendar alignment

US close (16:00 New York) is before the next Asian open. For every US trading date t, the **follower date** of an
Asian market is that market's first trading date strictly after t. Pairs with a gap of more than {max_gap} calendar
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
"""


def write_readme(universe, last_date):
    groups = universe.groupby("group").apply(lambda g: ", ".join(g.index))
    text = README.format(
        yf_version=yf.__version__, today=date.today().isoformat(), start=START, last=last_date,
        min_years=MIN_YEARS, max_gap=MAX_GAP_DAYS,
        g_leaders=groups["US AI leaders"], g_infra=groups["US AI infrastructure"],
        g_us_ctrl=groups["US non-AI controls"], g_asia_ai=groups["Asian AI followers"],
        g_asia_ctrl=groups["Asian non-AI controls"], g_bench=groups["Benchmark"])
    (DATA / "README.md").write_text(text)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--refresh", action="store_true", help="download again even if data/raw has the file")
    args = parser.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)

    # 1. download (or reuse data/raw)
    print(f"Downloading {len(ALL_TICKERS)} tickers from {START} ...")
    failed = download_all(ALL_TICKERS, args.refresh)
    raw = load_raw(ALL_TICKERS)
    universe = pd.DataFrame(universe_rows()).set_index("ticker")

    # 2. drop tickers with too little data (logged, not replaced)
    too_short = {t: len(df) for t, df in raw.items() if len(df) < MIN_YEARS * 252}
    raw = {t: df for t, df in raw.items() if t not in too_short}
    universe = universe.drop(index=list(failed) + list(too_short), errors="ignore")
    for t in [*failed, *too_short]:
        print(f"  DROPPED {t}: {'download failed' if t in failed else f'only {too_short[t]} days'}")

    # 3. clean and save
    prices, calendars, clean_log = clean(raw, universe)
    prices.to_csv(DATA / "prices_v2.csv", index=False)
    try:
        prices.to_parquet(DATA / "prices_v2.parquet", index=False)
    except Exception as e:                                     # parquet is a convenience; CSV is the reference copy
        print(f"  parquet not written ({e}); CSV is enough")
    universe.reset_index().to_csv(DATA / "universe.csv", index=False)

    # 4. calendar alignment for each Asian market, saved so the notebook uses exactly the same pairs
    us_days = calendars["US"]
    cal_rows, align_log = [], {}
    for market in ["JP", "KR", "TW"]:
        pairs, counts = align_calendars(us_days, calendars[market], MAX_GAP_DAYS)
        cal_rows.append(pairs.assign(market=market))
        align_log[market] = counts
        print(f"  {market}: {counts['kept']} US dates paired, dropped {counts['dropped_gap']} (gap > "
              f"{MAX_GAP_DAYS} days), {counts['dropped_clash']} (same follower date, earlier US date), "
              f"{counts['dropped_no_follower']} (no follower date yet)")
    pd.concat(cal_rows).to_csv(DATA / "calendar_v2.csv", index=False)

    # 5. log
    first_us = pd.Timestamp(START) + pd.Timedelta(days=7)
    late = {t: v["first_date"] for t, v in clean_log.items() if pd.Timestamp(v["first_date"]) > first_us}
    log = {"download_date": date.today().isoformat(), "start": START, "last_date": str(prices["date"].max().date()),
           "failed": failed, "dropped_too_short": too_short, "late_listed_kept": late,
           "alignment": align_log, "per_ticker": clean_log}
    (DATA / "download_log.json").write_text(json.dumps(log, indent=1))
    write_readme(universe, log["last_date"])
    print(f"  late listings kept: {late or 'none'}")
    print(f"  cleaning: {sum(v['rows_off_calendar_dropped'] for v in clean_log.values())} off-calendar rows dropped, "
          f"{sum(v['stale_rows_set_missing'] for v in clean_log.values())} stale rows set missing")

    # 6. sanity checks on the alignment: stop loudly if they fail
    results, problems = sanity_checks(prices, calendars)
    (OUT / "sanity.json").write_text(json.dumps({"checks": results, "problems": problems}, indent=1))
    print("\nSanity checks (correlation of SPY on US date t with the Asian index):")
    print(f"  {'index':7s} {'follower cc':>12s} {'follower oc':>12s} {'same day cc':>12s}")
    for idx, r in results.items():
        print(f"  {idx:7s} {r['corr_follower_cc']:12.3f} {r['corr_follower_oc']:12.3f} "
              f"{r['corr_same_calendar_day_cc']:12.3f}")
    print("Mean over each market's stocks (follower date):")
    print(f"  {'market':7s} {'cc':>12s} {'oc':>12s} {'gap (c->o)':>12s}")
    for idx, r in results.items():
        s = r["stocks"]
        print(f"  {idx:7s} {s['mean_corr_cc']:12.3f} {s['mean_corr_oc']:12.3f} {s['mean_corr_overnight_gap']:12.3f}")
    if problems:
        print("\nALIGNMENT SANITY CHECK FAILED:\n  " + "\n  ".join(problems))
        sys.exit(1)
    print("\nAll sanity checks passed. Files written to data/ and outputs/v2/.")
