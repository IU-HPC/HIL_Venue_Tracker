"""Validate venue metadata and edition events before generating artifacts."""

import argparse
import csv
import datetime as dt
from pathlib import Path
from urllib.parse import urlparse

from venue_data import (
    VALID_EVENT_STATUSES,
    VALID_EVENT_TYPES,
    VALID_SCOPES,
    VALID_VENUE_TYPES,
)


def valid_url(value):
    parsed = urlparse(value)
    return parsed.scheme in {'http', 'https'} and bool(parsed.netloc)


def read_rows(path):
    with open(path, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        if not reader.fieldnames:
            raise ValueError(f'{path}: missing header')
        return reader.fieldnames, list(reader)


def check_date(value, label, errors, required=False):
    if not value:
        if required:
            errors.append(f'{label}: date is required')
        return None
    try:
        return dt.date.fromisoformat(value)
    except ValueError:
        errors.append(f'{label}: invalid ISO date {value!r}')
        return None


def validate(venues_path='venues.csv', events_path='events.csv'):
    errors = []
    warnings = []
    _, venue_rows = read_rows(venues_path)
    _, event_rows = read_rows(events_path)
    venue_names = set()

    for line, row in enumerate(venue_rows, 2):
        label = f'{venues_path}:{line} ({row.get("name") or "unnamed"})'
        name = row.get('name', '').strip()
        if not name:
            errors.append(f'{label}: name is required')
        elif name in venue_names:
            errors.append(f'{label}: duplicate venue name')
        venue_names.add(name)
        if row.get('lab_scope') not in VALID_SCOPES:
            errors.append(f'{label}: invalid lab_scope {row.get("lab_scope")!r}')
        if row.get('venue_type') not in VALID_VENUE_TYPES:
            errors.append(f'{label}: invalid venue_type {row.get("venue_type")!r}')
        tags = [tag.strip() for tag in row.get('fit_tags', '').split(';') if tag.strip()]
        if not tags:
            errors.append(f'{label}: at least one fit tag is required')
        if not valid_url(row.get('url', '')):
            errors.append(f'{label}: valid official URL is required')
        notes_file = row.get('notes_file', '').strip()
        if notes_file and not Path(notes_file).is_file():
            errors.append(f'{label}: notes file does not exist: {notes_file}')
        for field in ('acceptance_rate_checked',):
            check_date(row.get(field, '').strip(), f'{label} {field}', errors)
        if row.get('acceptance_rate_5y') and not row.get('acceptance_rate_source'):
            errors.append(f'{label}: acceptance rate requires a source')
        if row.get('ccf_rank') and not row.get('ccf_year'):
            errors.append(f'{label}: CCF rank requires an edition year')
        if row.get('icore_rank') and not row.get('icore_year'):
            errors.append(f'{label}: ICORE rank requires an edition year')

    event_keys = set()
    for line, row in enumerate(event_rows, 2):
        venue = row.get('venue', '').strip()
        label = f'{events_path}:{line} ({venue or "unnamed"})'
        if venue not in venue_names:
            errors.append(f'{label}: unknown venue')
        event_type = row.get('event_type', '').strip()
        if event_type not in VALID_EVENT_TYPES:
            errors.append(f'{label}: invalid event_type {event_type!r}')
        if row.get('status') not in VALID_EVENT_STATUSES:
            errors.append(f'{label}: invalid status {row.get("status")!r}')
        start = check_date(row.get('start_date', '').strip(), label, errors,
                           required=row.get('status') != 'tba')
        end = check_date(row.get('end_date', '').strip(), f'{label} end_date', errors)
        verified = check_date(row.get('verified_on', '').strip(),
                              f'{label} verified_on', errors)
        if start and end and end < start:
            errors.append(f'{label}: end_date precedes start_date')
        key = (venue, row.get('edition'), event_type, row.get('start_date'))
        if key in event_keys:
            errors.append(f'{label}: duplicate event')
        event_keys.add(key)
        if row.get('status') == 'confirmed' and not verified:
            errors.append(f'{label}: confirmed event requires verified_on')
        if row.get('status') == 'confirmed' and not row.get('source_url'):
            errors.append(f'{label}: confirmed event requires source_url')
        if row.get('source_url') and not valid_url(row['source_url']):
            errors.append(f'{label}: invalid source_url')
        if row.get('status') != 'confirmed':
            warnings.append(f'{label}: {row.get("status")} date needs verification')

    return errors, warnings, len(venue_rows), len(event_rows)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Validate HIL venue tracker CSV data.')
    parser.add_argument('--venues', default='venues.csv')
    parser.add_argument('--events', default='events.csv')
    args = parser.parse_args()

    found_errors, found_warnings, venue_count, event_count = validate(
        args.venues, args.events)
    for error in found_errors:
        print(f'ERROR: {error}')
    for warning in found_warnings[:10]:
        print(f'WARNING: {warning}')
    if len(found_warnings) > 10:
        print(f'WARNING: ... and {len(found_warnings) - 10} more review items')
    print(f'Validated {venue_count} venues and {event_count} events: '
          f'{len(found_errors)} errors, {len(found_warnings)} review warnings')
    raise SystemExit(1 if found_errors else 0)
