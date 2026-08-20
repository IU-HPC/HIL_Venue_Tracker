# Contributing to HIL Venue Tracker

The most valuable contributions are confirming current edition dates, improving lab-fit notes, and recording submission details learned through experience. Keep the default view focused on venues the lab is genuinely likely to use.

## Before opening a pull request

```bash
python3 validate_data.py
python3 report.py --needs-review
python3 timeline_generator.py --no-show
python3 generate_ical.py
```

The validator treats malformed data as an error and unconfirmed dates as review warnings. Expected dates are allowed; they simply remain visible in the audit.

## Updating dates

Dates belong in `events.csv`, one row per deadline or conference date range:

```csv
venue,edition,event_type,start_date,end_date,deadline_time,timezone,status,location,source_url,verified_on,notes
MYVENUE,2027,deadline,2026-10-15,,23:59,AoE,confirmed,,https://official-cfp.example/,2026-08-20,Main track
MYVENUE,2027,conference,2027-05-20,2027-05-23,,,confirmed,"Boston, MA, USA",https://official-site.example/,2026-08-20,
```

Rules:

- Use the official venue website or CFP as the date source.
- Use ISO dates (`YYYY-MM-DD`). Do not infer a year from a global base year.
- `confirmed` requires both `source_url` and `verified_on`.
- Use `expected` for a planning estimate derived from a prior cycle.
- Use `tba` when an edition is known but no defensible date estimate exists; `start_date` may be blank.
- Record an end date for multi-day events.
- Record an exact deadline time and timezone when the CFP publishes them. Use `AoE` when the venue says Anywhere on Earth.
- Put track or cycle distinctions in `notes`.
- Never upgrade an expected date to confirmed merely because multiple aggregators repeat it.

## Adding a venue

Add one stable row to `venues.csv`. Do not add deadline metadata to this file.

```csv
name,full_name,lab_scope,venue_type,fit_tags,lab_fit_notes,url,notes_file,submission_cycle,presented_at,acceptance_rate_5y,acceptance_rate_window,acceptance_rate_source,acceptance_rate_checked,ccf_rank,ccf_year,ccf_field,icore_rank,icore_year,icore_field,ranking_notes
MYVENUE,My Example Venue,watch,conference,parallel-computing;data-reduction,Promote when the reduction algorithm is the primary contribution,https://official.example/,notes/MYVENUE.md,annual,,,,,,,,,,,,
```

### Choosing lab scope

| Scope | Guidance |
|---|---|
| `core` | The lab regularly considers it across multiple projects |
| `adjacent` | Useful for a narrower contribution type or audience |
| `watch` | Plausible candidate needing lab evaluation |

Begin uncertain venues in `watch`. Promotion is a lab judgment based on research fit and experience, not an automatic consequence of an external rank.

### Venue type

Use `conference`, `workshop`, or `journal`. Do not create a fake conference date for a rolling journal. Use `submission_cycle=rolling` and, when appropriate, `presented_at` to describe a journal-to-conference presentation relationship.

### Fit tags and notes

Tags should describe the contribution expected by the venue rather than repeat its title. Reuse existing spelling where possible:

```text
parallel-computing  data-reduction  scientific-applications  co-design
storage-io          data-movement   distributed-computing    workflows
architecture        hardware        compiler                 runtime
systems             data-management performance-modeling     compression
machine-learning    visualization   accelerators             data-analytics
```

`lab_fit_notes` should complete the sentence “Consider this venue when…”. Avoid reducing fit to a single numeric score.

### External signals

- Keep `ccf_rank` and `icore_rank` separate from `lab_scope`.
- Always record the ranking edition year.
- Preserve whether a source describes a conference or journal.
- Use `ranking_notes` for renamed venues, successor relationships, or ambiguous acronyms.
- Leave a field blank when a venue is absent; absence is not the same as “unranked.”

### Acceptance rates

Record the measurement window, source URL, and date checked. A mean acceptance rate is historical context, not an acceptance prediction. Do not mix short papers, workshop tracks, or desk rejections into a number unless the source does so and the caveat is documented.

## Venue notes

Copy `notes/TEMPLATE.md` to `notes/<VENUE>.md`. Notes are the lab-specific part of the tracker and should capture:

- Typical contribution and evaluation expectations
- Page limits, templates, and review model
- Rebuttal, revision, and artifact processes
- Travel support and co-located events
- Lab experience and recurring reviewer feedback

Leave unknown sections present rather than inventing details.

## Removing or demoting a venue

Do not erase useful history. Change `lab_scope` to `adjacent` or `watch`, explain the decision in `lab_fit_notes` or the notes file, and retain old edition events when they provide planning context.

## CSV conventions

- CSV quoting is supported; quote fields containing commas.
- Use semicolons only to separate `fit_tags`.
- Venue names are stable join keys and must match exactly between both CSV files and `targets.csv`.
- One venue may have multiple deadlines and multiple editions.
- Do not duplicate stable metadata in `events.csv`.

## What not to commit manually

- Personal `targets.csv` entries.
- Python caches or local environments.
- Hand-edited PNG or ICS output. The workflow regenerates tracked artifacts from the CSV data after changes.
