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
│       └── strikes_clean.parquet   # cleaned dataset -- not yet created, see Progress below
└── notebooks/
    ├── 01_data_profiling.ipynb     # session 1: structural profile, grain audit, missingness over
    │                                # time (corrected in session 3), outlier pass
    └── 02_data_cleaning.ipynb      # sessions 2-3: documented fixes -> data/processed/strikes_clean.parquet
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

**Session 2 (data cleaning) — logic complete and verified; output file not yet written.**
`notebooks/02_data_cleaning.ipynb` applies seven documented fixes (whitespace-only strings normalized to
null across every string column, added session 3; plus six from session 2 — missing-means-zero fills,
dropping the unused `TRANSFER` column, recoding `DAMAGE_LEVEL`'s blank to an explicit `"Unknown"`, ordered
categoricals for `NUM_SEEN`/`NUM_STRUCK`, one evidenced `SPEED` correction, and resolving all 15 corrupted
`LATITUDE`/`LONGITUDE` values). Three flagged issues are explicitly left alone with stated reasons. The
raw CSV is never modified. **`data/processed/strikes_clean.parquet` does not exist yet** — the notebook's
`to_parquet` and round-trip-check cells are correct but unexecuted, because the sandbox that built this
notebook has no `pyarrow` and no network access to install it. Running those two cells once, locally,
with `pip install -r requirements.txt` (which includes `pyarrow`), is the one step outside that sandbox
this project still needs.

**Session 3 (correction pass) — complete.** Fixed 3 of session 2's 4 open review items (the pandas pin,
a false claim in the `LATITUDE` reasoning, a validation check that couldn't fail) and re-confirmed the
parquet write is still blocked — same cause as session 2. Also traced and fixed the `TIME` measurement
error described above, including a cause investigation (concentrated in one source, an abrupt one-year
break, not a gradual drift).

**Session 4 (parquet resolution) — attempted, still blocked.** This session's only job was to get
`data/processed/strikes_clean.parquet` to actually exist. It doesn't yet: the sandbox producing these
notebooks still has no `pyarrow`, no `fastparquet`, and no network access to install either — confirmed a
third time, and independently confirmed by the session 3 review hitting the identical wall in its own,
separate environment. Two small documentation fixes did land this session (this paragraph's wording, and
a one-year-off boundary in notebook 01's corrected `TIME` summary). **The remaining step needs a real
local Python environment with network access** — `pip install -r requirements.txt`, then run
`02_data_cleaning.ipynb` top to bottom and confirm cells 26–27 execute — since no environment available to
produce these notebooks so far has had one.

**Next (session 5):** once `strikes_clean.parquet` exists for real, temporal EDA on the corrected basis —
seasonality and time-of-day, using the 2020–2023 `TIME` window now that "reliable from 2019 on" is known
not to hold.
