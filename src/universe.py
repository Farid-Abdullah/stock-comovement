"""Which stocks are in the study, which group each belongs to, and which index it is measured against.

Every group has a selection rule (written out in data/README.md) so we can answer "why these stocks".
"""

# (group name, market, home index, tickers). Market codes: US, TW (Taiwan), KR (Korea), JP (Japan).
GROUP_TABLE = [
    ("US AI leaders",        "US", "SPY",   ["NVDA", "AMD", "AVGO", "MU", "MSFT", "GOOGL", "META", "AMZN", "ORCL"]),
    ("US AI infrastructure", "US", "SPY",   ["SMCI", "VRT", "ANET", "MRVL", "COHR", "CLS", "VST", "DELL"]),
    ("US non-AI controls",   "US", "SPY",   ["JPM", "XOM", "PG", "KO", "WMT", "JNJ"]),
    ("Asian AI followers",   "TW", "^TWII", ["2330.TW", "2317.TW", "2382.TW", "3231.TW", "6669.TW", "2308.TW",
                                             "2454.TW", "3711.TW"]),
    ("Asian AI followers",   "KR", "^KS11", ["005930.KS", "000660.KS", "042700.KS"]),
    ("Asian AI followers",   "JP", "^N225", ["8035.T", "6857.T", "6146.T", "6920.T", "9984.T"]),
    ("Asian non-AI controls", "JP", "^N225", ["7203.T", "8306.T", "4502.T"]),
    ("Asian non-AI controls", "KR", "^KS11", ["005380.KS"]),
    ("Asian non-AI controls", "TW", "^TWII", ["2412.TW", "2882.TW"]),
]

# Benchmarks: market indices, plus VIX (US fear gauge) and SMH (semiconductor ETF) for later stages.
BENCHMARKS = {"SPY": "US", "^N225": "JP", "^KS11": "KR", "^TWII": "TW", "^VIX": "US", "SMH": "US"}
HOME_INDEX = {"US": "SPY", "TW": "^TWII", "KR": "^KS11", "JP": "^N225"}

# Company names, for tables and the economic interpretation of edges.
NAMES = {
    "NVDA": "Nvidia", "AMD": "AMD", "AVGO": "Broadcom", "MU": "Micron", "MSFT": "Microsoft", "GOOGL": "Alphabet",
    "META": "Meta", "AMZN": "Amazon", "ORCL": "Oracle",
    "SMCI": "Super Micro", "VRT": "Vertiv", "ANET": "Arista", "MRVL": "Marvell", "COHR": "Coherent",
    "CLS": "Celestica", "VST": "Vistra", "DELL": "Dell",
    "JPM": "JPMorgan", "XOM": "Exxon Mobil", "PG": "Procter & Gamble", "KO": "Coca-Cola", "WMT": "Walmart",
    "JNJ": "Johnson & Johnson",
    "2330.TW": "TSMC", "2317.TW": "Hon Hai (Foxconn)", "2382.TW": "Quanta", "3231.TW": "Wistron",
    "6669.TW": "Wiwynn", "2308.TW": "Delta Electronics", "2454.TW": "MediaTek", "3711.TW": "ASE Technology",
    "005930.KS": "Samsung Electronics", "000660.KS": "SK hynix", "042700.KS": "Hanmi Semiconductor",
    "8035.T": "Tokyo Electron", "6857.T": "Advantest", "6146.T": "Disco", "6920.T": "Lasertec",
    "9984.T": "SoftBank Group",
    "7203.T": "Toyota", "8306.T": "Mitsubishi UFJ", "4502.T": "Takeda", "005380.KS": "Hyundai Motor",
    "2412.TW": "Chunghwa Telecom", "2882.TW": "Cathay Financial",
}

# Approximate index weight of each Asian stock in its home index, used ONLY for the ex-stock robustness check:
#   r_ex = (r_index - w * r_stock) / (1 - w)
# Held constant over the whole sample (in reality weights drift; TSMC's share of ^TWII rose from about 30% to 40%).
# Author estimates from index-provider factsheets (TWSE, KRX, Nikkei), rounded; see data/README.md.
# ^N225 is price-weighted, so its "weight" is the stock's share of the price sum, not of market value.
INDEX_WEIGHTS = {
    "2330.TW": 0.35, "2317.TW": 0.03, "2382.TW": 0.01, "3231.TW": 0.005, "6669.TW": 0.005, "2308.TW": 0.02,
    "2454.TW": 0.04, "3711.TW": 0.01, "2412.TW": 0.01, "2882.TW": 0.01,
    "005930.KS": 0.20, "000660.KS": 0.08, "042700.KS": 0.003, "005380.KS": 0.02,
    "8035.T": 0.08, "6857.T": 0.05, "6146.T": 0.015, "6920.T": 0.01, "9984.T": 0.05,
    "7203.T": 0.01, "8306.T": 0.005, "4502.T": 0.01,
}


def universe_rows():
    """One row per ticker: ticker, market, group, home index, name, index weight (Asian stocks only)."""
    rows = []
    for group, market, index, tickers in GROUP_TABLE:
        for t in tickers:
            rows.append({"ticker": t, "market": market, "group": group, "home_index": index,
                         "name": NAMES[t], "index_weight": INDEX_WEIGHTS.get(t)})
    for t, market in BENCHMARKS.items():
        rows.append({"ticker": t, "market": market, "group": "Benchmark", "home_index": None,
                     "name": t, "index_weight": None})
    return rows


ALL_TICKERS = [r["ticker"] for r in universe_rows()]
