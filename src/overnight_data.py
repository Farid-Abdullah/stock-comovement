"""Calendar alignment, returns, residuals and items for the overnight-transmission study.

The key idea: the US market closes (16:00 New York) before the next Asian session opens. So US moves on US date t
can be paired with Asian moves on the next Asian trading date. `align_calendars` makes that pairing explicit.
Everything here uses only past data for betas and volatility (shifted by one day), so there is no look-ahead.
"""
import numpy as np
import pandas as pd


# ---- reshaping ------------------------------------------------------------------------------------------------

def wide(prices_long, field):
    """Long table (date, ticker, open, close, volume) -> wide table date x ticker for one field."""
    return prices_long.pivot(index="date", columns="ticker", values=field).sort_index()


# ---- calendar alignment ----------------------------------------------------------------------------------------

def align_calendars(us_dates, follower_dates, max_gap_days=4):
    """Pair every US trading date t with the follower market's first trading date strictly after t.

    Why "strictly after": an Asian session on calendar date t ends before the US opens on t, so it cannot react to
    the US session of t. The first Asian session that can is on the next Asian trading date.

    Two cleaning rules (each counted, so the caller can log them):
      * gap rule:   if the follower date is more than `max_gap_days` calendar days after t (a long Asian holiday),
                    the pair is dropped: a reaction after a week is not "overnight".
      * clash rule: if several US dates map to the same follower date (Asia was closed while the US traded),
                    only the LATEST US date is kept. The follower return then still spans the earlier US sessions,
                    which is why we cannot keep them as separate pairs.

    Returns (pairs, counts): pairs is a DataFrame with columns us_date, follower_date, gap_days (one row per kept
    US date, sorted), counts is {"us_dates", "kept", "dropped_gap", "dropped_clash", "dropped_no_follower"}.
    """
    us = pd.DatetimeIndex(sorted(set(pd.DatetimeIndex(us_dates).normalize())))
    fol = pd.DatetimeIndex(sorted(set(pd.DatetimeIndex(follower_dates).normalize())))
    pos = fol.searchsorted(us, side="right")              # index of the first follower date > t
    has_next = pos < len(fol)
    pairs = pd.DataFrame({"us_date": us[has_next], "follower_date": fol[pos[has_next]]})
    pairs["gap_days"] = (pairs["follower_date"] - pairs["us_date"]).dt.days

    n_no_follower = int((~has_next).sum())               # US dates after the last follower date in the data
    too_far = pairs["gap_days"] > max_gap_days
    n_gap = int(too_far.sum())
    pairs = pairs[~too_far]
    latest = ~pairs.duplicated("follower_date", keep="last")
    n_clash = int((~latest).sum())
    pairs = pairs[latest].reset_index(drop=True)

    assert (pairs["follower_date"] > pairs["us_date"]).all(), "follower date must be strictly after the US date"
    assert pairs["follower_date"].is_unique and pairs["us_date"].is_unique
    counts = {"us_dates": len(us), "kept": len(pairs), "dropped_gap": n_gap, "dropped_clash": n_clash,
              "dropped_no_follower": n_no_follower}
    return pairs, counts


# ---- returns ---------------------------------------------------------------------------------------------------

def simple_returns(close):
    """Close-to-close return on each local trading date (previous local close -> today's close)."""
    return close.pct_change(fill_method=None)


def local_returns(close_wide, open_wide, tickers, calendar):
    """cc, oc and overnight-gap returns for one market, computed on that market's OWN trading calendar.

    Why: the combined price table has the union of all markets' dates. Computing pct_change on it would put a
    missing day before every Asian date that follows a US-only date (and the reverse), turning those returns into
    NaN. So we first keep only the market's own dates, then take returns.
    """
    close = close_wide.loc[calendar, tickers]
    open_ = open_wide.loc[calendar, tickers]
    cc = simple_returns(close)
    oc = open_to_close(open_, close)
    gap = open_ / close.shift(1) - 1                      # previous local close -> today's open
    return cc, oc, gap


def open_to_close(open_, close):
    """Open-to-close return: the part of the day you could still trade after seeing the US close."""
    return close / open_ - 1


def follower_frame(follower_values, pairs):
    """Re-index a follower-market table (indexed by follower date) onto US dates using the aligned pairs.

    Row t of the result holds the follower's value on the follower date paired with US date t.
    US dates without a valid pair get NaN.
    """
    mapped = follower_values.reindex(pairs["follower_date"].to_numpy())
    mapped.index = pd.DatetimeIndex(pairs["us_date"].to_numpy(), name="us_date")
    return mapped


# ---- residuals and items (same definitions as lag_rules_models_regimes.ipynb) -----------------------------------

def rolling_beta(stock_ret, index_ret, window=252):
    """Beta of each stock to the index over the previous `window` days, shifted one day so today is not used."""
    var = index_ret.rolling(window).var()
    betas = {c: stock_ret[c].rolling(window).cov(index_ret) / var for c in stock_ret.columns}
    return pd.DataFrame(betas).shift(1)


def residuals(stock_ret, index_ret, window=252):
    """Stock return minus beta x index return: the stock-specific part of the move."""
    return stock_ret - rolling_beta(stock_ret, index_ret, window).mul(index_ret, axis=0)


def ex_stock_index(index_ret, stock_ret, weight):
    """Index return with one stock taken out: (r_index - w * r_stock) / (1 - w), with w held constant."""
    return (index_ret - weight * stock_ret) / (1 - weight)


def zscores(ret, vol_window=60):
    """Return divided by the stock's typical move (std of the previous `vol_window` days, shifted: no look-ahead)."""
    return ret / ret.rolling(vol_window).std().shift(1)


def move_items(z, z_k=1.0, suffix=""):
    """Boolean item table: TICKER_UP when z >= z_k, TICKER_DOWN when z <= -z_k. NaN z gives no item."""
    up = (z >= z_k)
    down = (z <= -z_k)
    up.columns = [f"{t}_UP{suffix}" for t in z.columns]
    down.columns = [f"{t}_DOWN{suffix}" for t in z.columns]
    return pd.concat([up, down], axis=1)


def volume_spike_items(volume, window=20, ratio=2.0, suffix=""):
    """Optional item: TICKER_VOLSPIKE when volume > ratio x the average of the previous `window` days."""
    avg = volume.rolling(window).mean().shift(1)
    spike = volume > ratio * avg
    spike.columns = [f"{t}_VOLSPIKE{suffix}" for t in volume.columns]
    return spike
