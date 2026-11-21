"""Round-trip trading costs per market, for intraday (open -> close) trades. Sources in data/README.md.

A round trip = buy at the open and sell at the close of the same session (or short and cover).
Cost = securities transaction tax on the sale (if any) + an assumed ~5 bps for fees and half-spreads.
"""
import pandas as pd

FEES_BPS = 5.0                    # brokerage fees + spread, assumed, per round trip (Korea, Taiwan)
JAPAN_ROUND_TRIP_BPS = 10.0       # Japan: no transaction tax; fees + spread, assumed

# Korea (KOSPI): securities transaction tax + special tax for rural development, combined, by start date.
KOREA_TAX_BPS = [
    ("2000-01-01", 30.0),         # 0.15% + 0.15% rural tax
    ("2019-05-30", 25.0),         # 0.10% + 0.15%
    ("2021-01-01", 23.0),         # 0.08% + 0.15%
    ("2023-01-01", 20.0),         # 0.05% + 0.15% (not confirmed against a source; see data/README.md)
    ("2024-01-01", 18.0),         # 0.03% + 0.15%
    ("2025-01-01", 15.0),         # 0.00% + 0.15%
    ("2026-01-01", 20.0),         # 0.05% + 0.15%
]

# Taiwan: securities transaction tax on the sale; same-session day trades pay half since 28 April 2017.
TAIWAN_TAX_BPS = [
    ("2000-01-01", 30.0),         # 0.30% normal rate
    ("2017-04-28", 15.0),         # 0.15% day-trade rate (extended in 2018, 2021 and 2024, currently to 2027)
]


def _rate_on(schedule, date):
    rate = schedule[0][1]
    for start, r in schedule:
        if pd.Timestamp(date) >= pd.Timestamp(start):
            rate = r
    return rate


def round_trip_bps(market, date):
    """Cost in basis points of one intraday round trip in `market` ("JP", "KR", "TW") on `date`."""
    if market == "JP":
        return JAPAN_ROUND_TRIP_BPS
    if market == "KR":
        return _rate_on(KOREA_TAX_BPS, date) + FEES_BPS
    if market == "TW":
        return _rate_on(TAIWAN_TAX_BPS, date) + FEES_BPS
    raise ValueError(f"unknown market {market}")


def cost_table(markets, dates):
    """DataFrame dates x markets of round-trip costs in bps (vectorised helper for the notebook)."""
    dates = pd.DatetimeIndex(dates)
    return pd.DataFrame({m: [round_trip_bps(m, d) for d in dates] for m in markets}, index=dates)
