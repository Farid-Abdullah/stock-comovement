"""Unit tests for the calendar alignment and the no-look-ahead rules. Run from the repo root: python -m pytest tests"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.overnight_data import (align_calendars, follower_frame, rolling_beta, zscores,   # noqa: E402
                                ex_stock_index, move_items)


def d(*days):
    return pd.to_datetime(list(days))


def pairs_dict(pairs):
    return {str(u.date()): str(f.date()) for u, f in zip(pairs["us_date"], pairs["follower_date"])}


def test_normal_week_maps_to_next_day():
    # Mon-Fri in both markets: US Monday -> Asian Tuesday, ..., US Thursday -> Asian Friday.
    us = d("2024-03-04", "2024-03-05", "2024-03-06", "2024-03-07")
    asia = d("2024-03-04", "2024-03-05", "2024-03-06", "2024-03-07", "2024-03-08")
    pairs, _ = align_calendars(us, asia)
    assert pairs_dict(pairs) == {"2024-03-04": "2024-03-05", "2024-03-05": "2024-03-06",
                                 "2024-03-06": "2024-03-07", "2024-03-07": "2024-03-08"}
    assert (pairs["gap_days"] == 1).all()


def test_same_calendar_date_is_never_the_follower():
    # The Asian session on date t ends before the US opens on t, so it must not be paired with US date t.
    pairs, _ = align_calendars(d("2024-03-05"), d("2024-03-05", "2024-03-06"))
    assert pairs_dict(pairs) == {"2024-03-05": "2024-03-06"}


def test_friday_maps_to_monday():
    pairs, _ = align_calendars(d("2024-03-08"), d("2024-03-08", "2024-03-11"))
    assert pairs_dict(pairs) == {"2024-03-08": "2024-03-11"}
    assert pairs["gap_days"].iloc[0] == 3


def test_long_holiday_is_dropped():
    # Lunar New Year: Taiwan closed for a week -> gap of 6 days > 4 -> dropped and counted.
    us = d("2024-02-07", "2024-02-14")
    asia = d("2024-02-07", "2024-02-15")
    pairs, counts = align_calendars(us, asia, max_gap_days=4)
    assert pairs_dict(pairs) == {"2024-02-14": "2024-02-15"}
    assert counts["dropped_gap"] == 1


def test_clash_keeps_latest_us_date():
    # Asia closed Tue-Wed: US Mon, Tue and Wed all point to Asian Thursday; keep only US Wednesday.
    us = d("2024-04-29", "2024-04-30", "2024-05-01")
    asia = d("2024-04-29", "2024-05-02")
    pairs, counts = align_calendars(us, asia)
    assert pairs_dict(pairs) == {"2024-05-01": "2024-05-02"}
    assert counts["dropped_clash"] == 2


def test_us_holiday_has_no_row_and_next_us_day_still_pairs():
    # US closed on Thursday (Thanksgiving): Wednesday -> Asian Thursday, Friday -> Asian Monday.
    us = d("2024-11-27", "2024-11-29")
    asia = d("2024-11-27", "2024-11-28", "2024-11-29", "2024-12-02")
    pairs, _ = align_calendars(us, asia)
    assert pairs_dict(pairs) == {"2024-11-27": "2024-11-28", "2024-11-29": "2024-12-02"}


def test_last_us_date_without_follower_is_counted():
    pairs, counts = align_calendars(d("2024-03-07", "2024-03-08"), d("2024-03-08"))
    assert pairs_dict(pairs) == {"2024-03-07": "2024-03-08"}
    assert counts["dropped_no_follower"] == 1


def test_follower_frame_moves_values_onto_us_dates():
    pairs, _ = align_calendars(d("2024-03-04", "2024-03-05"), d("2024-03-05", "2024-03-06"))
    values = pd.DataFrame({"X": [1.0, 2.0]}, index=d("2024-03-05", "2024-03-06"))
    out = follower_frame(values, pairs)
    assert list(out.index) == list(d("2024-03-04", "2024-03-05"))
    assert out["X"].tolist() == [1.0, 2.0]


def test_beta_and_zscore_do_not_look_ahead():
    # Changing a future return must not change today's beta or z-score denominator.
    rng = np.random.default_rng(0)
    idx = pd.bdate_range("2020-01-01", periods=400)
    m = pd.Series(rng.normal(0, 0.01, 400), index=idx)
    s = pd.DataFrame({"A": 1.2 * m + rng.normal(0, 0.01, 400)}, index=idx)
    beta, z = rolling_beta(s, m, 252), zscores(s, 60)
    s2, m2 = s.copy(), m.copy()
    s2.iloc[300:] *= 10                        # shock everything from day 300 on
    m2.iloc[300:] *= -5
    beta2, z2 = rolling_beta(s2, m2, 252), zscores(s2, 60)
    pd.testing.assert_frame_equal(beta.iloc[:301], beta2.iloc[:301])   # day 300's beta uses days 48..299 only
    pd.testing.assert_frame_equal(z.iloc[:300], z2.iloc[:300])


def test_ex_stock_index_removes_the_stock():
    # If the index is 40% stock A and 60% "rest" with the rest flat, the ex-stock index is flat.
    r_stock = pd.Series([0.05, -0.02])
    r_index = 0.4 * r_stock
    assert np.allclose(ex_stock_index(r_index, r_stock, 0.4), 0)


def test_move_items_thresholds():
    z = pd.DataFrame({"A": [1.2, -1.0, 0.5, np.nan]})
    items = move_items(z, 1.0, "+1")
    assert items["A_UP+1"].tolist() == [True, False, False, False]
    assert items["A_DOWN+1"].tolist() == [False, True, False, False]


def test_local_returns_ignore_other_markets_dates():
    # The combined table has a US-only date (Asia closed) between two Asian dates. The Asian return on the
    # following date must still be computed from the previous ASIAN close, not become NaN.
    from src.overnight_data import local_returns
    dates = d("2024-04-29", "2024-04-30", "2024-05-01")      # 30 Apr: US only
    close = pd.DataFrame({"ASIA": [100.0, np.nan, 110.0], "US": [50.0, 51.0, 52.0]}, index=dates)
    open_ = close.copy()
    open_["ASIA"] = [99.0, np.nan, 105.0]
    cc, oc, gap = local_returns(close, open_, ["ASIA"], d("2024-04-29", "2024-05-01"))
    assert np.isclose(cc.loc["2024-05-01", "ASIA"], 0.10)
    assert np.isclose(gap.loc["2024-05-01", "ASIA"], 0.05)
    assert np.isclose(oc.loc["2024-05-01", "ASIA"], 110 / 105 - 1)


def test_round_trip_costs():
    from src.costs import round_trip_bps
    assert round_trip_bps("JP", "2024-05-01") == 10
    assert round_trip_bps("TW", "2017-04-27") == 35 and round_trip_bps("TW", "2017-04-28") == 20
    assert round_trip_bps("KR", "2025-06-01") == 20 and round_trip_bps("KR", "2026-02-01") == 25
    assert round_trip_bps("KR", "2019-05-29") == 35 and round_trip_bps("KR", "2019-05-30") == 30
