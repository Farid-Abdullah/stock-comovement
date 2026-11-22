"""Large-font PNG versions of four figures from final_project.ipynb.

This script does NOT build a PowerPoint. It redraws four saved results with bigger fonts so they stay
readable on a slide or in a two-column report:
    placebo.png   ChatGPT placebo test (two of the four measures)
    models.png    rule-survival models vs one-feature baselines (ROC-AUC)
    affinity.png  significant changes in AI affinity, with bootstrap intervals
    groups.png    mean pair lift inside and between groups over time

Run after final_project.ipynb (it reads the CSV files that the notebook writes to outputs/final/):
    python make_slide_figures.py
Writes outputs/final/slides/*.png and refreshes the six figures in report/figures/.
No new analysis happens here.
"""
from pathlib import Path
import shutil

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

OUT = Path("outputs/final")
SLIDES = OUT / "slides"
SLIDES.mkdir(exist_ok=True)
INK, SOFT, MUTED, AXIS, SURFACE, RED = "#0b0b0b", "#52514e", "#898781", "#c3c2b7", "#fcfcfb", "#b3261e"
GROUP_COLORS = {"AI enablers": "#2a78d6", "Big Tech": "#eb6834", "Traditional software": "#1baf7a", "Non-tech baseline": "#898781"}
CHATGPT = pd.Timestamp("2022-12-01")
plt.rcParams.update({
    "figure.facecolor": SURFACE, "axes.facecolor": SURFACE, "savefig.facecolor": SURFACE, "font.size": 17,
    "axes.titlesize": 19, "axes.titleweight": "bold", "axes.titlelocation": "left", "axes.edgecolor": AXIS,
    "axes.spines.top": False, "axes.spines.right": False, "xtick.color": AXIS, "ytick.color": AXIS,
    "xtick.labelcolor": SOFT, "ytick.labelcolor": SOFT, "axes.labelcolor": SOFT, "grid.color": "#e1e0d9",
    "lines.linewidth": 2.6, "savefig.dpi": 150, "savefig.bbox": "tight",
})


def years(ax):
    ax.xaxis.set_major_locator(mdates.YearLocator(2))
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))


# Placebo test: two panels only (rule turnover, tech change minus control).
placebo = pd.read_csv(OUT / "placebo_break_test.csv", index_col=0, parse_dates=True)
fig, axes = plt.subplots(2, 1, figsize=(11, 6.4), sharex=True, layout="constrained")
for ax, col, title in [(axes[0], "rule_turnover", "Rule turnover, year before vs year after"),
                       (axes[1], "tech_change_minus_control", "Tech-pair change minus control-pair change")]:
    pct = (placebo[col] <= placebo.loc[CHATGPT, col]).mean()
    ax.plot(placebo.index, placebo[col], color="#2a78d6", marker="o", markersize=3.5, lw=1.6)
    ax.scatter([CHATGPT], [placebo.loc[CHATGPT, col]], color=RED, s=110, zorder=5)
    ax.set_title(f"{title}: ChatGPT (red) is above only {pct:.0%} of {len(placebo)} dates", fontsize=17)
    ax.grid(axis="y")
years(axes[1])
fig.savefig(SLIDES / "placebo.png")

# Model comparison: ROC-AUC only.
res = pd.read_csv(OUT / "survival_model_results.csv", index_col=0)
res = res.rename(index=lambda s: s.replace("baseline: ", ""))
fig, ax = plt.subplots(figsize=(11, 6.2), layout="constrained")
names = res.index.tolist()
y = np.arange(len(names))[::-1]
models = ["logistic regression", "random forest", "gradient boosting"]
ax.barh(y, res["ROC-AUC"], color=["#2a78d6" if n in models else AXIS for n in names], height=0.7)
for yy, v in zip(y, res["ROC-AUC"]):
    ax.text(v + 0.006, yy, f"{v:.2f}", va="center", fontsize=17, color=INK)
ax.set_yticks(y, names, fontsize=17)
ax.set_xlim(0.4, 0.72)
ax.axvline(0.5, color=RED, ls=":", lw=1.5)
ax.set_xlabel("ROC-AUC on post-ChatGPT windows (0.5 = no skill)")
ax.set_title("Models (blue) vs one-feature baselines (grey)")
fig.savefig(SLIDES / "models.png")

# AI affinity change: significant stocks plus a few for contrast.
chg = pd.read_csv(OUT / "ai_affinity_change.csv", index_col=0)
show = chg[chg["significant"]].sort_values("change")
fig, ax = plt.subplots(figsize=(11, 6.6), layout="constrained")
y = np.arange(len(show))
cols = [GROUP_COLORS[g] for g in show["group"]]
ax.hlines(y, show["ci_low"], show["ci_high"], color=cols, lw=4, alpha=0.45)
ax.scatter(show["change"], y, color=cols, s=110, zorder=3, edgecolor=INK)
ax.axvline(0, color=AXIS)
ax.set_yticks(y, show.index, fontsize=16)
for t, lab in zip(show.index, ax.get_yticklabels()):
    lab.set_color(GROUP_COLORS[chg.loc[t, "group"]])
ax.set_xlabel("change in AI affinity, latest 2 years minus 2 years before ChatGPT")
ax.set_title("Significant changes only (95% bootstrap interval, FDR 5%)")
handles = [plt.Line2D([], [], marker="o", ls="", color=c, markersize=11, label=g) for g, c in GROUP_COLORS.items()]
ax.legend(handles=handles, frameon=False, fontsize=14, loc="lower right")
ax.grid(axis="x")
fig.savefig(SLIDES / "affinity.png")

# Group lift over time: the four lines that tell the story.
blocks = pd.read_csv(OUT / "group_block_lift_over_time.csv", index_col=0, parse_dates=True)
fig, ax = plt.subplots(figsize=(11, 6.2), layout="constrained")
for col, c, label in [("AI-AI", "#2a78d6", "AI - AI"), ("Software-Software", "#1baf7a", "Software - Software"),
                      ("AI-Software", "#7a4fc9", "AI - Software"), ("Baseline-Baseline", MUTED, "Control - Control")]:
    ax.plot(blocks.index, blocks[col], color=c, label=label)
    ax.text(blocks.index[-1] + pd.Timedelta(days=40), blocks[col].iloc[-1], label, color=c, fontsize=15, va="center")
ax.axhline(1, color=AXIS)
ax.axvline(CHATGPT, color=RED, ls="--", lw=1.5)
ax.text(CHATGPT, ax.get_ylim()[1], " ChatGPT", color=RED, va="top", fontsize=15)
ax.set_ylabel("mean pair lift (1 = chance)")
ax.set_xlim(blocks.index[0], blocks.index[-1] + pd.Timedelta(days=900))
ax.set_xticks([pd.Timestamp(f"{y}-01-01") for y in range(2018, 2027, 2)], [str(y) for y in range(2018, 2027, 2)])
ax.grid(axis="y")
ax.set_title("Mean pair lift inside and between groups (one-year windows)")
fig.savefig(SLIDES / "groups.png")
# Refresh report/figures/: three of the large-font figures plus three notebook figures used as they are.
REPORT_FIGURES = Path("report/figures")
for name in ["placebo.png", "groups.png", "affinity.png"]:
    shutil.copy(SLIDES / name, REPORT_FIGURES / name)
for name in ["4_1_rules_per_window_by_mode.png", "7_1_survival_by_feature.png", "8_1_anomaly_timeline.png"]:
    shutil.copy(OUT / name, REPORT_FIGURES / name)
print("wrote", sorted(p.name for p in SLIDES.glob("*.png")), "and refreshed report/figures/")
