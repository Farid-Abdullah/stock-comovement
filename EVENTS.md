# Event layer: which events break co-movement, and do the breaks last?

`events.ipynb` is the main analysis of the project. It builds on `final_project.ipynb`, which supplies the
baseline (market-adjusted items, rolling-window rules, the Isolation Forest scores and the ChatGPT placebo table).

## Files

| File | What it is |
|---|---|
| `build_events.py` | Builds the event calendar. Run once. `--earnings` also downloads earnings dates. |
| `data/events.csv` | 368 events: 89 FOMC rate decisions, 130 CPI releases, 130 jobs reports, 19 one-off shocks. Each row has its source link. The last FOMC row (9 Dec 2026) is after the data ends, so the notebook uses 88. |
| `data/earnings_dates.csv` | Earnings dates for the 40 stocks, created by `python build_events.py --earnings` (needs internet access to Yahoo Finance). Included. |
| `events.ipynb` | The analysis, sections 1 to 9, with a "Results at a glance" table at the top. Runs in about 30 seconds. |
| `outputs/events/` | Every table (CSV) and figure (PNG) from the notebook, plus `key_numbers_events.json`. |

## How to run

```bash
pip install -r requirements.txt
jupyter nbconvert --to notebook --execute --inplace final_project.ipynb   # first: events.ipynb reads two of its tables
jupyter nbconvert --to notebook --execute --inplace events.ipynb
```

Run from the repo root. The notebook reads `data/prices.csv`, `data/events.csv`, `data/earnings_dates.csv`,
`outputs/final/placebo_break_test.csv` and `outputs/final/top_anomalous_days.csv`. Both data files are included,
so `python build_events.py` is only needed to rebuild them. Without the earnings file, Section 5 (earnings
spillover) and the earnings categories are skipped and everything else runs.

## Where the event dates come from

* **FOMC**: Federal Reserve meeting calendars (2021–2026) and the "historical materials by year" pages (2016–2020).
  The decision day is the second day of each meeting. Emergency cuts on 3 Mar 2020 and Sunday 15 Mar 2020 are
  included; notation votes are not.
* **CPI and jobs reports**: the BLS news-release archives; the release date is in each file name. The 2025
  government shutdown is reflected: no October 2025 CPI or jobs report, and delayed releases in Oct–Dec 2025.
* **Shocks**: 19 hand-picked events, each linked to a news report or an official release (OpenAI, Nvidia,
  Oracle, USTR, Pfizer) that confirms the date. The list is a biased sample (chosen because the market moved),
  so the scheduled events are the fair test.

## Main design choices

* Items, residual returns and the Isolation Forest are identical to `final_project.ipynb`. The notebook checks
  that its top-12 unusual days match the final notebook's table.
* **Event-date shift test**: the whole calendar moves by a random number of trading days (1,000 times), which
  keeps its rhythm and breaks only the link between events and market days.
* **A category for every unusual day**: shock, scheduled release, earnings reaction, market stress, earnings day
  with a quiet reporter, or unexplained (first rule that applies; Section 3). Descriptive, not a test.
* **Local break score**: 1 − correlation of the 780 pair lifts in the half-year before vs after each week.
* **Recovery curves (H2)**: similarity of post-event half-years to the pre-event half-year, measured against
  normal drift. The classification rule is written in Section 7 before the results.
* **Earnings rules** are compared with the same company's big moves on non-earnings days, so a rule only counts
  if earnings add something beyond normal co-movement.

## Known limits

* Half-year windows cannot see breaks that last only a few weeks.
* The local break score is noisier in the first and last half-year of the sample.
* Shocks after mid-2025 have less than a year of data after them, so H2 marks them "too recent". DeepSeek
  (Jan 2025) is classified from only four second-year points, the minimum the rule allows.
* H2 counts change with the settings (Section 8), so treat them as suggestive.
