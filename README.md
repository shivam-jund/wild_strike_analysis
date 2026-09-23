# Wildlife Strike Analysis

Exploratory analysis of the FAA National Wildlife Strike Database — voluntary reports of collisions
between US civil aircraft and wildlife (overwhelmingly birds, with some terrestrial mammals), filed by
pilots, airlines, and airport staff since 1990.

## Dataset

- **Source:** [FAA National Wildlife Strike Database](https://wildlife.faa.gov/) (`Public.csv` extract)
- **Size:** 354,144 rows x 102 columns (~200 MB)
- **Time span:** 1990–2026 (2026 is partial, and recent months are likely undercounted further due to
  reporting lag on top of that)
- **Field reference:** the FAA publishes an official field dictionary at
  [wildlife.faa.gov/assets/fieldlist.pdf](https://wildlife.faa.gov/assets/fieldlist.pdf). A handful of
  column names in this extract differ slightly from that reference (e.g. this file's `PHASE_OF_FLIGHT` vs.
  FAA's `PHASE_OF_FLT`, `NUM_SEEN`/`NUM_STRUCK` vs. `BIRDS_SEEN`/`BIRDS_STRUCK`) — don't assume a 1:1 name
  match without checking.

**Important caveat:** this is voluntary, self-reported data, not a census of all wildlife strikes — the
FAA's own estimate is that fewer than 40% of strikes are reported in a given year. Reporting completeness
also varies by airport and operator, and has changed substantially over the dataset's 36-year span (see
the profiling notebook for specifics). Raw counts by airport, airline, or year mix true strike risk with
air-traffic volume and reporting diligence — treat a raw ranking as a risk ranking with that caveat
attached, not on its own.

## Getting the data

`Public.csv` is tracked with [Git LFS](https://git-lfs.com) (see `.gitattributes`). After cloning, pull
the actual file contents with:

```bash
git lfs install
git lfs pull
```

## Repository structure

```
wild_strike_analysis/
├── README.md
├── requirements.txt
├── .gitignore                      (existing)
├── .gitattributes                  (existing — routes *.csv/*.xlsx/*.zip through Git LFS)
├── data/
│   ├── procured/
│   │   └── Public.csv              # FAA National Wildlife Strike Database extract (LFS), raw, untouched
│   └── processed/
│       └── strikes_clean.pkl.gz    # cleaned dataset (pickle+gzip -- see Progress, session 4)
└── notebooks/
    ├── 01_data_profiling.ipynb     # session 1: structural profile, grain audit, missingness over
    │                                # time (corrected in session 3), outlier pass
    ├── 02_data_cleaning.ipynb      # sessions 2-4: documented fixes -> data/processed/strikes_clean.pkl.gz
    └── 03_temporal_eda.ipynb       # session 5: seasonality and hour-of-day
```

`src/`, a `sql/` folder, and a `reports/` folder are deliberately not created yet — each will be added in
the session it's first needed rather than scaffolded empty up front.

## Setup

```bash
python -m venv venv
source venv/bin/activate   # venv\Scripts\activate on Windows
pip install -r requirements.txt
jupyter notebook
```

## Progress

**Session 1 (data profiling) — complete, with one correction.** `notebooks/01_data_profiling.ipynb`
establishes: `INDEX_NR` is safe to treat as one-row-per-report; the large apparent duplication under
`(INCIDENT_DATE, AIRPORT_ID, OPERATOR, FLT)` is mostly a side effect of grouping on a mostly-blank `FLT`
column rather than real duplicate reports or genuine multi-strike flights; and a short, specific list of
outlier rows in `SPEED`, `HEIGHT`, and `COST_REPAIRS`. **Its original conclusion about `TIME`'s
reliability was wrong** — `.notna()` counted 31,298 whitespace-only `TIME` values as "filled." The
corrected picture (session 3): `TIME` is genuinely reliable only for 2020–2023, and collapses again to
~55–59% for 2024–2026, concentrated almost entirely in one reporting source (`FAA Form 5200-7-E`), with no
usable `TIME_OF_DAY` fallback for those rows. See the correction section in the notebook for the full
before/after.

**Session 2 (data cleaning) — complete.** `notebooks/02_data_cleaning.ipynb` applies seven documented
fixes (whitespace-only strings normalized to null across every string column, added session 3; plus six
from session 2 — missing-means-zero fills, dropping the unused `TRANSFER` column, recoding
`DAMAGE_LEVEL`'s blank to an explicit `"Unknown"`, ordered categoricals for `NUM_SEEN`/`NUM_STRUCK`, one
evidenced `SPEED` correction, and resolving all 15 corrupted `LATITUDE`/`LONGITUDE` values). Three flagged
issues are explicitly left alone with stated reasons. The raw CSV is never modified.

**Session 3 (correction pass) — complete.** Fixed 3 of session 2's 4 open review items (the pandas pin,
a false claim in the `LATITUDE` reasoning, a validation check that couldn't fail) and traced and fixed the
`TIME` measurement error described above, including a cause investigation (concentrated in one source, an
abrupt one-year break, not a gradual drift).

**Session 4 (parquet resolution) — complete, via a format substitution.** `data/processed/strikes_clean.pkl.gz`
now exists for real. The original plan — parquet, via `pyarrow` — never ran across three sessions, because
every environment producing these notebooks lacked both `pyarrow` and network access to install it, and
waiting for that to change wasn't going to work. Session 4 replaced the final write with
`to_pickle(compression='gzip')`, which needs only the standard library: 32.8 MB (smaller than the raw
CSV), reloads in under 2 seconds. **Trade-off, accepted deliberately:** pickle is Python/pandas-specific —
not readable from R, not queryable directly by a SQL engine. Parquet remains the better long-term format;
this is a documented substitution to unblock a single-consumer pipeline, reversible in two lines if network
access ever becomes available. `requirements.txt` no longer lists `pyarrow`.

**Session 5 (temporal EDA) — complete.** `notebooks/03_temporal_eda.ipynb` is the project's first notebook
to read from the cleaned data rather than `Public.csv`. **Seasonality** (1990-2025, each month's share of
its own year, to isolate shape from the volume-growth trend): a single broad season — trough in
January-February, a local peak in May followed by a June dip, sustained peak across July-October (four
months carrying roughly half the year's strikes), decline through November-December. Stable in shape
across the full span, though the summer peak has sharpened and winter's share has eased somewhat from the
1990s to recent years. **Hour-of-day**, restricted to 2020-2023 (the one window `TIME` is genuinely
reliable): one clear peak at 08:00, climbing from a 3-5am trough and declining gradually through the rest
of the day. A `TIME`-vs-`TIME_OF_DAY` cross-check validates both fields against each other — clean
agreement at midday/overnight, blurry (as expected) at dawn and dusk.

**Next:** species, size, and damage distributions; phase-of-flight and altitude patterns; geographic
concentration.
