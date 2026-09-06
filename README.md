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
├── .gitignore                    (existing)
├── .gitattributes                (existing — routes *.csv/*.xlsx/*.zip through Git LFS)
├── data/
│   └── procured/
│       └── Public.csv            # FAA National Wildlife Strike Database extract (LFS)
└── notebooks/
    └── 01_data_profiling.ipynb   # session 1: structural profile, grain audit,
                                   # missingness over time, outlier pass
```

`src/`, `data/processed/`, a `sql/` folder, and a `reports/` folder are deliberately not created yet —
each will be added in the session it's first needed rather than scaffolded empty up front.

## Setup

```bash
python -m venv venv
source venv/bin/activate   # venv\Scripts\activate on Windows
pip install -r requirements.txt
jupyter notebook
```

## Progress

**Session 1 (data profiling) — complete.** `notebooks/01_data_profiling.ipynb` establishes: `INDEX_NR` is
safe to treat as one-row-per-report; the large apparent duplication under
`(INCIDENT_DATE, AIRPORT_ID, OPERATOR, FLT)` is mostly a side effect of grouping on a mostly-blank `FLT`
column rather than real duplicate reports or genuine multi-strike flights; which fields are and aren't
safe to use for a 1990–2025 trend, and why; and a short, specific list of outlier rows in `SPEED`,
`HEIGHT`, and `COST_REPAIRS`.

**Next (session 2):** EDA proper — temporal patterns (respecting the reporting-volume confound),
species/size/damage distributions, phase-of-flight and altitude patterns, geographic concentration.
