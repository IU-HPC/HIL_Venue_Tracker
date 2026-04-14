# HIL Venue Tracker

A lightweight tool for tracking HPC conference submission deadlines and event dates. Generates a visual timeline, text reports, and a calendar export to help lab members plan paper submissions throughout the year.

## Setup

Requires Python 3 and `matplotlib`:

```bash
pip install matplotlib
```

---

## Tools

### Timeline (`timeline_generator.py`)

Generates a visual PNG timeline showing deadlines and conference dates sorted by earliest deadline.

```bash
python timeline_generator.py                        # tier-1 venues only (default)
python timeline_generator.py --show-all             # include non-tier-1 venues (shown faded)
python timeline_generator.py --output my_plot.png   # custom output path
python timeline_generator.py --no-show              # save without opening a viewer (CI/headless)
```

Output: `conference_timeline.png`

- Diamond markers (◆) = paper deadlines, with the date above and short notes below (e.g. "Cycle 1")
- Star markers (★) = conference dates
- Venues sorted top-to-bottom by earliest upcoming deadline
- Non-tier-1 venues rendered faded when using `--show-all`

---

### Text Report (`report.py`)

Prints a deadline summary to the terminal with urgency coloring, acceptance rates, and targeting info.

```bash
python report.py                             # tier-1 venues, sorted by earliest deadline
python report.py --show-all                  # include non-tier-1 venues (dimmed)
python report.py --approx                    # only venues with approximate dates (verification audit)
python report.py --next 5                    # 5 nearest upcoming deadlines (compact view)
python report.py --until 2026-12-31          # deadlines on or before this date
python report.py --since 2026-10-01          # deadlines on or after this date
python report.py --since 2026-10-01 --until 2026-12-31  # date window
```

Deadline urgency coloring: red = within 30 days, yellow = within 60 days, gray = further out or passed.

#### Targeting papers (`targets.csv`)

To flag which conferences you are actively targeting for a specific paper or project, add entries to [`targets.csv`](targets.csv):

```
venue,paper,notes
SC,compression paper,targeting Apr 8 deadline
IPDPS,checkpoint work,waiting on benchmark results
```

- `venue` must match the short name in `conferences.csv` (e.g. `SC`, `IPDPS`)
- Multiple papers can target the same venue; one paper can target multiple venues
- Targets appear as `>> Targeting:` lines in the full report and as a `★` marker in `--next`
- `targets.csv` is personal — don't commit targeting entries for your own papers to the shared repo

---

### Calendar Export (`generate_ical.py`)

Exports deadlines and conference dates to an `.ics` file. Each **deadline** event includes a **30-day advance reminder** so it appears in your calendar automatically.

```bash
python generate_ical.py                         # tier-1 venues only
python generate_ical.py --show-all              # include non-tier-1 venues
python generate_ical.py --output my_cal.ics     # custom output path
```

Output: `deadlines.ics`

| App | How to subscribe |
|-----|-----------------|
| Google Calendar | Settings → Add calendar → From URL (or import the file) |
| Apple Calendar | File → Import |
| Outlook | File → Open & Export → Import/Export |

Tip: if your calendar app supports subscribing to a URL, point it at the raw `deadlines.ics` in the repository and it will stay updated automatically whenever the file is regenerated.

---

## Data

All conference data lives in [`conferences.csv`](conferences.csv). Each row represents a single event — either a paper deadline or the conference date — for a given venue.

### CSV Schema

| Field | Description |
|-------|-------------|
| `name` | Short venue name (e.g. `SC`, `IPDPS`) |
| `full_name` | Full official venue name |
| `tier1` | `true` = shown in default view; `false` = hidden unless `--show-all` is used |
| `tier` | `top`, `regular`, or `workshop` |
| `event_type` | `conference` or `deadline` |
| `month` | Month of the event (1–12) |
| `day` | Day of the event |
| `year_offset` | Offset from `BASE_YEAR` in `timeline_generator.py`: `0` = base year, `-1` = prior year |
| `url` | CFP or conference homepage |
| `notes` | Short inline note (≤14 chars shows on the plot; avoid commas, use semicolons) |
| `notes_file` | Path to the long-form notes file, e.g. `notes/SC.md` |
| `acceptance_rate` | Approximate historical acceptance rate, e.g. `~18%` |

### Tracked Venues

**Tier-1 — shown by default**

| Venue | Tier | Acceptance |
|-------|------|-----------|
| SC | Top | N/A |
| IPDPS | Top | N/A |
| PPoPP | Top | N/A |
| ASPLOS | Top | N/A |
| HPCA | Top | N/A |
| TACO | Top | N/A (rolling review; presented at MICRO) |
| HPDC | Regular | N/A |
| ICS | Regular | N/A |
| ICDCS | Regular | N/A |
| USENIX ATC | Regular | N/A |
| SigMetrics | Regular | N/A |

**Non-tier-1 — tracked but hidden by default (`--show-all` to display)**

SIGMOD, VLDB, MSST, ICPP, ICDE, DRBSD

### Venue notes

Each venue has a long-form notes file in [`notes/`](notes/) covering submission format, review process, and lab tips. The short `notes` CSV column is for one-liner flags only; anything longer belongs in the markdown file. Use [`notes/TEMPLATE.md`](notes/TEMPLATE.md) when adding a new venue.

### Updating for a new year

1. Update `BASE_YEAR` at the top of `timeline_generator.py` (coordinate with the lab first).
2. Verify and update dates in `conferences.csv` — check each venue's CFP page.
3. Update `url` fields if CFP pages have changed.
4. Run `python report.py --approx` to quickly audit which venues still have approximate dates.
5. Commit and open a PR (see [CONTRIBUTING.md](CONTRIBUTING.md)).

---

## Automation

A GitHub Actions workflow ([`.github/workflows/update-timeline.yml`](.github/workflows/update-timeline.yml)) automatically regenerates `conference_timeline.png`, `conference_timeline_all.png`, and `deadlines.ics` whenever `conferences.csv` changes on `main`. Lab members who don't run the tools locally will always see a current plot and calendar file in the repository.

To enable: go to **Settings → Actions → General → Workflow permissions** and set to **Read and write**.

---

## See also

[Architecture & System Conference Deadlines](https://casys-kaist.github.io/?sub=ARCH,SYS,ML,OTHER,TBD) — a related community-maintained tracker.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for how to add venues, update dates, and submit changes.
