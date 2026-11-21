"""Build the event calendar for events.ipynb.

    python build_events.py              # writes data/events.csv (no internet needed)
    python build_events.py --earnings   # also downloads earnings dates with yfinance -> data/earnings_dates.csv

data/events.csv has one row per event:
    date        the trading day the market could first react (see REACTION DAY below)
    announced   the calendar date of the announcement
    event_type  FOMC | CPI | NFP | SHOCK
    name        short description
    category    for SHOCK rows: ai_launch | ai_business | macro | policy | geopolitical | health | market
    source      where the date comes from
    checked     True when the date was checked against the source while building this file

REACTION DAY
    FOMC decisions are announced at 2:00 p.m. ET, so the market reacts the same day.
    CPI and jobs reports (NFP) are released at 8:30 a.m. ET, before the open: same day.
    An announcement on a weekend or holiday is moved to the next trading day (done in the notebook,
    which knows the trading calendar). Example: the Fed's Sunday 15 March 2020 cut -> Monday 16 March.
    Earnings: after the close (4 p.m. ET or later) -> next trading day; otherwise the same day.
"""
from pathlib import Path
import argparse
import sys

import pandas as pd

DATA = Path("data")

# ---------------------------------------------------------------------------------------------
# FOMC decision days (second day of each two-day meeting, plus unscheduled rate decisions).
# Sources: Federal Reserve meeting calendars (2021-2026) and "FOMC historical materials by year"
# pages (2016-2020). Notation votes and conference calls without a rate decision are left out.
# ---------------------------------------------------------------------------------------------
FOMC_SOURCE_RECENT = "https://www.federalreserve.gov/monetarypolicy/fomccalendars.htm"
FOMC_SOURCE_OLD = "https://www.federalreserve.gov/monetarypolicy/fomchistorical{year}.htm"
FOMC = {
    2016: ["01-27", "03-16", "04-27", "06-15", "07-27", "09-21", "11-02", "12-14"],
    2017: ["02-01", "03-15", "05-03", "06-14", "07-26", "09-20", "11-01", "12-13"],
    2018: ["01-31", "03-21", "05-02", "06-13", "08-01", "09-26", "11-08", "12-19"],
    2019: ["01-30", "03-20", "05-01", "06-19", "07-31", "09-18", "10-30", "12-11"],
    # 2020: 3 Mar emergency cut (statement 3 Mar); Sunday 15 Mar emergency cut; 17-18 Mar meeting cancelled.
    2020: ["01-29", "03-03", "03-15", "04-29", "06-10", "07-29", "09-16", "11-05", "12-16"],
    2021: ["01-27", "03-17", "04-28", "06-16", "07-28", "09-22", "11-03", "12-15"],
    2022: ["01-26", "03-16", "05-04", "06-15", "07-27", "09-21", "11-02", "12-14"],
    2023: ["02-01", "03-22", "05-03", "06-14", "07-26", "09-20", "11-01", "12-13"],
    2024: ["01-31", "03-20", "05-01", "06-12", "07-31", "09-18", "11-07", "12-18"],
    2025: ["01-29", "03-19", "05-07", "06-18", "07-30", "09-17", "10-29", "12-10"],
    2026: ["01-28", "03-18", "04-29", "06-17", "07-29", "09-16", "10-28", "12-09"],
}
FOMC_NOTES = {"2020-03-03": "emergency cut (unscheduled)", "2020-03-15": "emergency cut on a Sunday (unscheduled)"}

# ---------------------------------------------------------------------------------------------
# CPI release dates, read from the file names in the BLS archive (cpi_MMDDYYYY.htm).
# Note the 2025 government shutdown: September CPI came out on 24 Oct 2025, October CPI was never
# published, and November CPI came out on 18 Dec 2025.
# ---------------------------------------------------------------------------------------------
CPI_SOURCE = "https://www.bls.gov/bls/news-release/cpi.htm"
CPI = """
01202016 02192016 03162016 04142016 05172016 06162016 07152016 08162016 09162016 10182016 11172016 12152016
01182017 02152017 03152017 04142017 05122017 06142017 07142017 08112017 09142017 10132017 11152017 12132017
01122018 02142018 03132018 04112018 05102018 06122018 07122018 08102018 09132018 10112018 11142018 12122018
01112019 02132019 03122019 04102019 05102019 06122019 07112019 08132019 09122019 10102019 11132019 12112019
01142020 02132020 03112020 04102020 05122020 06102020 07142020 08122020 09112020 10132020 11122020 12102020
01132021 02102021 03102021 04132021 05122021 06102021 07132021 08112021 09142021 10132021 11102021 12102021
01122022 02102022 03102022 04122022 05112022 06102022 07132022 08102022 09132022 10132022 11102022 12132022
01122023 02142023 03142023 04122023 05102023 06132023 07122023 08102023 09132023 10122023 11142023 12122023
01112024 02132024 03122024 04102024 05152024 06122024 07112024 08142024 09112024 10102024 11132024 12112024
01152025 02122025 03122025 04102025 05132025 06112025 07152025 08122025 09112025 10242025 12182025
01132026 02132026 03112026 04102026 05122026 06102026 07142026 08122026 09112026 10142026 11102026
""".split()

# ---------------------------------------------------------------------------------------------
# Employment Situation (jobs report, NFP) release dates from the BLS archive (empsit_MMDDYYYY.htm).
# 2025 shutdown: no October 2025 release; September data came out 20 Nov, November data 16 Dec 2025.
# ---------------------------------------------------------------------------------------------
NFP_SOURCE = "https://www.bls.gov/bls/news-release/empsit.htm"
NFP = """
01082016 02052016 03042016 04012016 05062016 06032016 07082016 08052016 09022016 10072016 11042016 12022016
01062017 02032017 03102017 04072017 05052017 06022017 07072017 08042017 09012017 10062017 11032017 12082017
01052018 02022018 03092018 04062018 05042018 06012018 07062018 08032018 09072018 10052018 11022018 12072018
01042019 02012019 03082019 04052019 05032019 06072019 07052019 08022019 09062019 10042019 11012019 12062019
01102020 02072020 03062020 04032020 05082020 06052020 07022020 08072020 09042020 10022020 11062020 12042020
01082021 02052021 03052021 04022021 05072021 06042021 07022021 08062021 09032021 10082021 11052021 12032021
01072022 02042022 03042022 04012022 05062022 06032022 07082022 08052022 09022022 10072022 11042022 12022022
01062023 02032023 03102023 04072023 05052023 06022023 07072023 08042023 09012023 10062023 11032023 12082023
01052024 02022024 03082024 04052024 05032024 06072024 07052024 08022024 09062024 10042024 11012024 12062024
01102025 02072025 03072025 04042025 05022025 06062025 07032025 08012025 09052025 11202025 12162025
01092026 02112026 03062026 04032026 05082026 06052026 07022026 08072026 09042026 10022026 11062026
""".split()

# ---------------------------------------------------------------------------------------------
# One-off shocks. These are chosen BECAUSE they were big market stories, so they are a biased
# sample; the scheduled events above are the unbiased test. The AI rows are the five events
# already used in final_project.ipynb (AI_EVENTS). `checked` = date verified against the source
# while building this file; the others are well-known dates that still need a source link.
# ---------------------------------------------------------------------------------------------
SHOCKS = [
    # date (first trading reaction day), name, category, source, checked
    ("2016-06-24", "Brexit referendum result", "geopolitical", "", False),
    ("2016-11-09", "US election result (Trump)", "policy", "", False),
    ("2018-02-05", "Volatility spike ('Volmageddon'), Dow -1,175", "market",
     "https://money.cnn.com/2018/02/05/investing/vix-volatility-index-dow/index.html", True),
    ("2018-03-22", "US announces tariffs on Chinese imports (Section 301)", "policy", "", False),
    ("2019-08-05", "China lets the yuan fall below 7 per dollar; worst day of 2019", "policy",
     "https://www.npr.org/2019/08/05/748236662/stock-markets-take-another-hit-as-the-trade-war-with-china-heats-up", True),
    ("2020-02-24", "COVID-19 sell-off begins (outbreak in Italy)", "health", "", False),
    ("2020-03-16", "COVID crash day after the Fed's Sunday emergency cut", "health", "", False),
    ("2020-11-09", "Pfizer vaccine efficacy result", "health", "", False),
    ("2022-02-24", "Russia invades Ukraine", "geopolitical", "", False),
    ("2022-11-30", "ChatGPT released", "ai_launch", "final_project.ipynb AI_EVENTS", True),
    ("2023-03-10", "Silicon Valley Bank collapse", "market", "", False),
    ("2023-03-14", "GPT-4 announced", "ai_launch", "final_project.ipynb AI_EVENTS", True),
    ("2023-05-25", "Nvidia's AI revenue guidance", "ai_business", "final_project.ipynb AI_EVENTS", True),
    ("2024-08-05", "Global sell-off, yen carry-trade unwind", "market",
     "https://fortune.com/2024/08/05/5-reasons-stocks-down-global-stock-market-rout/", True),
    ("2024-11-06", "US election result (Trump)", "policy", "", False),
    ("2025-01-27", "DeepSeek sell-off", "ai_business", "final_project.ipynb AI_EVENTS", True),
    ("2025-04-03", "'Liberation Day' tariffs announced (2 Apr after the close)", "policy",
     "https://www.pbs.org/newshour/economy/u-s-stock-market-tumbles-the-day-after-trumps-major-tariff-announcement", True),
    ("2025-04-09", "90-day tariff pause rally", "policy", "", False),
    ("2025-09-10", "Oracle's $455bn cloud backlog", "ai_business", "final_project.ipynb AI_EVENTS", True),
]


def from_mmddyyyy(codes):
    return [pd.Timestamp(f"{c[4:]}-{c[:2]}-{c[2:4]}") for c in codes]


def build_events():
    rows = []
    for year, days in FOMC.items():
        src = FOMC_SOURCE_RECENT if year >= 2021 else FOMC_SOURCE_OLD.format(year=year)
        for md in days:
            d = f"{year}-{md}"
            rows.append({"announced": d, "event_type": "FOMC", "name": "FOMC rate decision " + FOMC_NOTES.get(d, ""),
                         "category": "macro", "source": src, "checked": True})
    for d in from_mmddyyyy(CPI):
        rows.append({"announced": d.date().isoformat(), "event_type": "CPI", "name": "CPI release",
                     "category": "macro", "source": CPI_SOURCE, "checked": True})
    for d in from_mmddyyyy(NFP):
        rows.append({"announced": d.date().isoformat(), "event_type": "NFP", "name": "Jobs report (Employment Situation)",
                     "category": "macro", "source": NFP_SOURCE, "checked": True})
    for d, name, cat, src, ok in SHOCKS:
        rows.append({"announced": d, "event_type": "SHOCK", "name": name, "category": cat, "source": src, "checked": ok})
    ev = pd.DataFrame(rows)
    ev["name"] = ev["name"].str.strip()
    ev["announced"] = pd.to_datetime(ev["announced"])
    return ev.sort_values(["announced", "event_type"]).reset_index(drop=True)


def fetch_earnings(tickers, limit=60):
    """Download earnings dates with yfinance. Needs internet access to Yahoo Finance.

    Returns one row per (ticker, earnings timestamp) with the reported time, so the notebook can tell
    whether the company reported before the open (react same day) or after the close (react next day).
    """
    import yfinance as yf
    out = []
    for t in tickers:
        try:
            df = yf.Ticker(t).get_earnings_dates(limit=limit)
        except Exception as e:  # network errors, delisted tickers, Yahoo changes
            print(f"  {t}: failed ({type(e).__name__}: {e})", file=sys.stderr)
            continue
        if df is None or df.empty:
            print(f"  {t}: no earnings dates returned", file=sys.stderr)
            continue
        df = df.reset_index().rename(columns={df.index.name or "index": "timestamp"})
        ts = pd.to_datetime(df["timestamp"])
        if ts.dt.tz is not None:
            ts = ts.dt.tz_convert("America/New_York").dt.tz_localize(None)
        surprise_col = next((c for c in df.columns if "Surprise" in c), None)
        out.append(pd.DataFrame({
            "ticker": t,
            "timestamp": ts,
            "reported_eps": df.get("Reported EPS"),
            "eps_estimate": df.get("EPS Estimate"),
            "surprise_pct": df[surprise_col] if surprise_col else None,
        }))
        print(f"  {t}: {len(df)} dates, {ts.min().date()} to {ts.max().date()}")
    if not out:
        return pd.DataFrame(columns=["ticker", "timestamp", "reported_eps", "eps_estimate", "surprise_pct"])
    earn = pd.concat(out, ignore_index=True)
    earn = earn[earn["reported_eps"].notna()]          # drop future (not yet reported) dates
    return earn.sort_values(["ticker", "timestamp"]).reset_index(drop=True)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--earnings", action="store_true", help="also download earnings dates with yfinance")
    args = parser.parse_args()
    DATA.mkdir(exist_ok=True)

    ev = build_events()
    ev.to_csv(DATA / "events.csv", index=False)
    print(f"data/events.csv: {len(ev)} events")
    print(ev.groupby("event_type").agg(n=("announced", "size"), first=("announced", "min"), last=("announced", "max")))

    if args.earnings:
        prices = pd.read_csv(DATA / "prices.csv", index_col=0, nrows=1)
        tickers = [t for t in prices.columns if t != "SPY"]
        print(f"Downloading earnings dates for {len(tickers)} tickers ...")
        earn = fetch_earnings(tickers)
        earn.to_csv(DATA / "earnings_dates.csv", index=False)
        print(f"data/earnings_dates.csv: {len(earn)} rows for {earn['ticker'].nunique()} tickers")
        if earn["ticker"].nunique() < len(tickers):
            print("Some tickers are missing; the notebook uses whatever is in the file.")


if __name__ == "__main__":
    main()
