"""Next-day association rules: mining, chance baseline, out-of-sample scoring.

Same method as lag_rules_models_regimes.ipynb (Lu, Han & Feng 1998 "inter-transaction" rules), rewritten without
notebook globals so the same functions serve every leader -> follower group:
  * a basket row is one US trading date t: leader items on t, follower items on the follower date (tagged '+1');
  * a rule is {leader items on t} -> {one follower item}, mined with FP-Growth;
  * chance baseline: shift the follower block in time (keeps every item's frequency, breaks the t -> t+1 link);
  * out of sample: score each rule on a later year it never saw, and compare with its mirror rule (same antecedent,
    opposite-direction consequent) to separate "predicts the direction" from "predicts a big move either way".
"""
import math

import numpy as np
import pandas as pd
from mlxtend.frequent_patterns import fpgrowth
from scipy.stats import hypergeom

FUT = "+1"


def ticker_of(item):
    return item.replace(FUT, "").rsplit("_", 1)[0]


def direction_of(item):
    return item.replace(FUT, "").rsplit("_", 1)[1]


def mirror(item):
    # NVDA_UP+1 <-> NVDA_DOWN+1
    return item.replace("_UP", "_TMP").replace("_DOWN", "_UP").replace("_TMP", "_DOWN")


def extended_basket(leader_items, follower_items):
    """Join leader items (columns like NVDA_UP) and follower items (2330.TW_UP) row by row, tagging followers '+1'.

    Both tables must already be indexed by the US date t (follower items moved onto t by the calendar alignment).
    """
    assert leader_items.index.equals(follower_items.index), "leader and follower rows must be the same US dates"
    fol = follower_items.copy()
    fol.columns = [f"{c}{FUT}" for c in fol.columns]
    return pd.concat([leader_items, fol], axis=1).fillna(False).astype(bool)


def n_possible_rules(n_leader_items, n_follower_items, max_antecedent=2):
    """How many rules of the form {1 or 2 leader items} -> {1 follower item} exist: the BH denominator."""
    n_ante = sum(math.comb(n_leader_items, k) for k in range(1, max_antecedent + 1))
    return n_ante * n_follower_items


def mine_lag_rules(basket, min_support, min_confidence, min_lift, max_len=3):
    """FP-Growth, then keep rules whose consequent is exactly one follower item and antecedent only leader items.

    Each rule gets a one-sided hypergeometric p-value: P(at least this many co-occurrences | independence).
    """
    itemsets = fpgrowth(basket, min_support=min_support, use_colnames=True, max_len=max_len)
    support = dict(zip(itemsets["itemsets"], itemsets["support"]))
    n = len(basket)
    rows = []
    for itemset, sup in support.items():
        future = [i for i in itemset if i.endswith(FUT)]
        if len(itemset) < 2 or len(future) != 1:
            continue                                        # need >= 1 leader item and exactly 1 follower item
        cons = future[0]
        ante = itemset - {cons}
        conf = sup / support[ante]
        base = support[frozenset([cons])]
        lift = conf / base
        if conf < min_confidence or lift < min_lift:
            continue
        n_ante, n_both, n_cons = round(support[ante] * n), round(sup * n), round(base * n)
        p = hypergeom.sf(n_both - 1, n, n_cons, n_ante)
        rows.append({"antecedent": tuple(sorted(ante)), "consequent": cons, "support": sup, "confidence": conf,
                     "base_rate": base, "lift": lift, "n_ante": n_ante, "n_both": n_both, "p_value": p})
    rules = pd.DataFrame(rows)
    if rules.empty:
        return rules
    rules["rule"] = rules["antecedent"].apply(" & ".join) + " -> " + rules["consequent"]
    rules["n_ante_items"] = rules["antecedent"].apply(len)
    return rules.sort_values("lift", ascending=False).reset_index(drop=True)


def bh_significant(p_values, m_total, q=0.05):
    """Benjamini-Hochberg over m_total POSSIBLE rules (rules that were never mined count as p = 1)."""
    p = np.asarray(p_values, dtype=float)
    if len(p) == 0:
        return np.zeros(0, dtype=bool)
    order = np.argsort(p)
    passed = p[order] <= q * np.arange(1, len(p) + 1) / m_total
    k = np.max(np.nonzero(passed)[0]) + 1 if passed.any() else 0
    out = np.zeros(len(p), dtype=bool)
    out[order[:k]] = True
    return out


def time_shift_null(basket, rng, min_shift=21):
    """Chance baseline: circularly shift the follower block by a random number of days (at least a month).

    Keeps every item's frequency and the leader-side structure, but breaks the real t -> follower-date link.
    """
    fut = [c for c in basket.columns if c.endswith(FUT)]
    n = len(basket)
    shift = int(rng.integers(min_shift, n - min_shift))
    null = basket.copy()
    null[fut] = np.roll(basket[fut].to_numpy(), shift, axis=0)
    return null


# ---- out-of-sample scoring ------------------------------------------------------------------------------------

def rule_day_matrices(rules, test_basket):
    """Boolean (test days x rules) matrices: antecedent fired, consequent happened, mirror consequent happened."""
    col = {c: i for i, c in enumerate(test_basket.columns)}
    X = test_basket.to_numpy()
    fired = np.ones((len(X), len(rules)), dtype=bool)
    for j, ante in enumerate(rules["antecedent"]):
        for a in ante:
            fired[:, j] &= X[:, col[a]]
    hit = X[:, [col[c] for c in rules["consequent"]]]
    hit_mirror = X[:, [col[mirror(c)] for c in rules["consequent"]]]
    return fired, hit, hit_mirror


def lifts_from_counts(fired, hit, hit_mirror, weights=None):
    """Test confidence, lift and mirror lift; `weights` (one per day) lets the bootstrap reuse the same matrices."""
    w = np.ones(len(fired)) if weights is None else weights
    n_fired = w @ fired
    with np.errstate(invalid="ignore", divide="ignore"):
        conf = (w @ (fired & hit)) / n_fired
        conf_m = (w @ (fired & hit_mirror)) / n_fired
        base = (w @ hit) / w.sum()
        base_m = (w @ hit_mirror) / w.sum()
        return n_fired, conf, conf / base, conf_m / base_m, base


def evaluate_out_of_sample(rules, test_basket, min_fired=5):
    """Score every rule on days it never saw. A rule is 'scored' if its antecedent fired at least `min_fired` times.

    direction_right compares LIFTS, not confidences, because UP and DOWN moves are not equally common.
    """
    if rules.empty or len(test_basket) == 0:
        return rules
    fired, hit, hit_mirror = rule_day_matrices(rules, test_basket)
    n_fired, conf, lift, lift_m, base = lifts_from_counts(fired, hit, hit_mirror)
    out = rules.copy()
    out["test_fired"], out["test_confidence"], out["test_base_rate"] = n_fired, conf, base
    out["test_lift"], out["test_mirror_lift"] = lift, lift_m
    out["scored"] = n_fired >= min_fired
    out["direction_right"] = out["test_lift"] > out["test_mirror_lift"]
    return out


def summarise(scored):
    """Headline numbers for a set of scored rules (only rules with enough test firings count)."""
    s = scored[scored["scored"]] if len(scored) else scored
    if len(s) == 0:
        return {"n_scored": 0, "median_test_lift": np.nan, "share_test_lift_gt_1": np.nan,
                "share_direction_right": np.nan, "share_mirror_also_gt_1": np.nan}
    return {"n_scored": int(len(s)),
            "median_test_lift": float(s["test_lift"].median()),
            "share_test_lift_gt_1": float((s["test_lift"] > 1).mean()),
            "share_direction_right": float(s["direction_right"].mean()),
            "share_mirror_also_gt_1": float((s["test_mirror_lift"] > 1).mean())}


def single_part_test_lifts(rule, test_basket):
    """Test lift of each one-item part of a two-item antecedent (same consequent), for the pair-vs-single test."""
    X = test_basket
    hit = X[rule["consequent"]].to_numpy()
    base = hit.mean()
    out = []
    for a in rule["antecedent"]:
        f = X[a].to_numpy()
        out.append((hit & f).sum() / f.sum() / base if f.sum() and base else np.nan)
    return out
