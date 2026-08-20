# HIL Venue Tracker

A lightweight, lab-focused tool for deciding when and where to publish work in parallel computation, data reduction, and application/computing co-design. It combines upcoming deadlines with research fit, lab context, external rankings, historical selectivity, and source-verification status.

This is intentionally not a comprehensive CS conference directory. The default view stays limited to venues the HIL lab commonly considers.

## Quick start

Requires Python 3 and `matplotlib`:

```bash
python3 -m pip install matplotlib
python3 report.py --next 5
python3 timeline_generator.py --no-show
python3 generate_ical.py
```

Validate the data before committing changes:

```bash
python3 validate_data.py
```

## Lab scopes

External reputation and lab relevance are deliberately separate.

| Scope | Meaning |
|---|---|
| `core` | Regularly useful for the lab; shown by default |
| `adjacent` | Relevant for particular contribution types |
| `watch` | Candidate venue to investigate and promote when appropriate |

CCF and ICORE ranks are independent evidence fields. They do not control lab scope. For example, a focused workshop can be highly useful to the lab without appearing in either ranking system.

## Tools

### Decision report (`report.py`)

```bash
python3 report.py                                      # core lab scope
python3 report.py --scope adjacent                     # adjacent venues only
python3 report.py --scope all                          # every scope
python3 report.py --fit data-reduction                 # matching research fit
python3 report.py --fit data-reduction,scientific-applications
python3 report.py --scope watch --fit storage-io       # investigate candidates
python3 report.py --next 5                             # nearest deadlines
python3 report.py --needs-review                       # stale/unverified dates
python3 report.py --since 2026-10-01 --until 2027-03-31
```

`--fit` keeps venues matching at least one requested tag and sorts stronger matches first. The report explains why each venue fits, shows external signals separately, and labels dates as `confirmed`, `expected`, or `TBA`.

`--show-all` remains as an alias for `--scope all`; `--approx` remains as an alias for `--needs-review`.

#### Targeting papers (`targets.csv`)

Create a local `targets.csv` to flag active plans:

```csv
venue,paper,notes
SC,compression paper,targeting the April deadline
IPDPS,checkpoint work,waiting on benchmark results
```

Venue names must match `venues.csv`. Targets are personal and gitignored. They appear in reports but are not shared with the lab.

### Timeline (`timeline_generator.py`)

```bash
python3 timeline_generator.py --no-show
python3 timeline_generator.py --scope adjacent --output adjacent.png --no-show
python3 timeline_generator.py --scope all --output conference_timeline_all.png --no-show
```

- Diamonds are paper deadlines; stars are venue start dates.
- Hollow markers mean expected or unverified; date labels remain plain positive dates.
- Colors show lab scope, not prestige.
- Venue labels show available CCF and ICORE tiers independently.
- Journals and watchlist entries without dated events do not appear on the timeline.

### Calendar export (`generate_ical.py`)

```bash
python3 generate_ical.py
python3 generate_ical.py --scope all --output all-deadlines.ics
```

Deadline events include a 30-day reminder. Expected dates are explicitly labeled `[EXPECTED]` in the calendar. Multi-day venue events use their full date range when known.

## Data model

The data is split so stable venue knowledge is not duplicated on every deadline.

### `venues.csv`

One row per publication venue.

| Field | Purpose |
|---|---|
| `name`, `full_name` | Stable identity |
| `lab_scope` | `core`, `adjacent`, or `watch` |
| `venue_type` | `conference`, `workshop`, or `journal` |
| `fit_tags` | Semicolon-separated research facets used by `--fit` |
| `lab_fit_notes` | Short explanation of when the lab should consider it |
| `url`, `notes_file` | Official landing page and local long-form notes |
| `submission_cycle`, `presented_at` | Annual/rolling behavior and journal presentation relationship |
| `acceptance_rate_5y`, source fields | Sourced historical selectivity with window and check date |
| `ccf_*`, `icore_*` | Independent rank, edition year, and field classification |
| `ranking_notes` | Alias, type, or interpretation caveats |

`fit_tags` are facets, not a magic score. Useful current tags include `parallel-computing`, `data-reduction`, `scientific-applications`, `co-design`, `storage-io`, `architecture`, `runtime`, `systems`, and `workflows`.

### `events.csv`

One row per edition-specific deadline or venue event.

| Field | Purpose |
|---|---|
| `venue`, `edition` | Links the event to `venues.csv` and an edition |
| `event_type` | `deadline` or `conference` |
| `start_date`, `end_date` | Explicit ISO dates; `end_date` supports multi-day events |
| `deadline_time`, `timezone` | Optional exact deadline time and zone, including AoE when stated |
| `status` | `confirmed`, `expected`, or `tba` |
| `location` | City/country or virtual/hybrid description |
| `source_url`, `verified_on` | Provenance and last human verification date |
| `notes` | Cycle, track, or uncertainty note |

All dates migrated from the old base-year tracker are currently marked `expected`. Most inherited links referenced 2026 editions while the calculated events represented the 2027 cycle. Run `python3 report.py --needs-review` to work through them; do not silently treat carried-forward dates as confirmed.

## Current venue set

The default `conference_timeline.png` uses `--scope core`: it is the lab-curated shortlist of recurring venues with the strongest general fit for HIL research. `core` describes lab relevance, not conference quality or an external rank. Core journals remain in the data and reports but do not appear in the timeline because they have no conference date.

**Core:** SC, IPDPS, PPoPP, ASPLOS, HPCA, TACO, TPDS, HPDC, ICS, ICDCS, SIGOPS ATC, SIGMETRICS, PASC.

**Adjacent:** SIGMOD, VLDB, MSST, ICPP, ICDE, DRBSD, CLUSTER, HiPC, IEEE BigData, IWBDR.

**Watch:** FAST, CCGRID, e-Science, PACT, CGO, MICRO, ISCA, EuroSys, OSDI, DCC, MASCOTS, IEEE VIS, ISC.

Watch entries do not receive speculative deadlines. Confirmed edition events may be recorded for planning, but promotion remains a lab decision based on recurring research fit.

## External reference sources

These sources support discovery and cross-checking; the official venue CFP remains authoritative for dates and submission rules.

- [Oxford Ranked Conference List](https://www.cs.ox.ac.uk/people/michael.wooldridge/conferences.html) — broad legacy discovery list with older field classifications; useful for finding names, not current deadlines.
- [Computer Science Conference Publication Stats](https://csconferences.org/) — rolling five-year acceptance-rate summaries for selected venues. Rates in `venues.csv` record this source and the date checked.
- [CCF Recommended International Conferences and Journals](https://ccf.atom.im/) — Chinese Computer Federation A/B/C classifications. The relevant field `计算机体系结构/并行与分布计算/存储系统` is stored in English as `architecture-parallel-distributed-storage`; conference and journal types remain distinct.
- [CORE/ICORE Conference Portal](https://portal.core.edu.au/) and [ranking documentation](https://www.core.edu.au/conference-portal) — independent A*/A/B/C and Field of Research classifications. Stored values use the 2026 ICORE edition.
- [FZ/SZ publication record](https://fzframework.org/publications/) — community evidence for where scientific data-reduction work has actually appeared. It informs fit and scope decisions but is not treated as a ranking or an acceptance-rate dataset.

Another useful community deadline reference is [Architecture & System Conference Deadlines](https://casys-kaist.github.io/?sub=ARCH,SYS,ML,OTHER,TBD).

## Updating an edition

1. Open the official CFP—not a ranking or deadline aggregator.
2. Add or update explicit rows in `events.csv`.
3. Use `status=confirmed` only with `source_url` and `verified_on`.
4. Record the full venue date range, location, deadline time, and timezone when published.
5. Run `python3 validate_data.py` and `python3 report.py --needs-review`.
6. Regenerate the timeline and calendar or let GitHub Actions do it after merge.

There is no global base-year rollover. Multiple editions and years can coexist in `events.csv`.

## Automation

The GitHub Actions workflow in [`.github/workflows/update-timeline.yml`](.github/workflows/update-timeline.yml) validates the CSV files and regenerates `conference_timeline.png`, `conference_timeline_all.png`, and `deadlines.ics` when venue data or generator code changes, monthly, or on manual request.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for data rules and examples.
