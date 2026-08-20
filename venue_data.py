"""Shared data loading and filtering for the HIL Venue Tracker."""

from __future__ import annotations

import csv
import datetime as dt


VALID_SCOPES = ('core', 'adjacent', 'watch')
VALID_VENUE_TYPES = ('conference', 'workshop', 'journal')
VALID_EVENT_TYPES = ('deadline', 'conference')
VALID_EVENT_STATUSES = ('confirmed', 'expected', 'tba')


def parse_date(value: str) -> dt.date | None:
    value = (value or '').strip()
    return dt.date.fromisoformat(value) if value else None


def selected_scopes(scope: str) -> set[str]:
    if scope == 'all':
        return set(VALID_SCOPES)
    if scope not in VALID_SCOPES:
        raise ValueError(f'Unknown lab scope: {scope}')
    return {scope}


def load_venues(venues_path='venues.csv', events_path='events.csv', scope='core'):
    """Load stable venue metadata and join edition-specific events."""
    scopes = selected_scopes(scope)
    venues = {}

    with open(venues_path, newline='', encoding='utf-8') as f:
        for row in csv.DictReader(f):
            row = {key: (value or '').strip() for key, value in row.items()}
            if row['lab_scope'] not in scopes:
                continue
            row['fit_tags'] = [
                tag.strip().lower()
                for tag in row.get('fit_tags', '').split(';')
                if tag.strip()
            ]
            row['events'] = []
            row['deadlines'] = []
            row['conference_event'] = None
            row['conference'] = None
            row['conference_end'] = None
            venues[row['name']] = row

    with open(events_path, newline='', encoding='utf-8') as f:
        for row in csv.DictReader(f):
            name = (row.get('venue') or '').strip()
            if name not in venues:
                continue
            event = {key: (value or '').strip() for key, value in row.items()}
            event['start_date'] = parse_date(event.get('start_date', ''))
            event['end_date'] = parse_date(event.get('end_date', ''))
            event['verified_on'] = parse_date(event.get('verified_on', ''))
            venues[name]['events'].append(event)

    for venue in venues.values():
        venue['events'].sort(
            key=lambda event: (
                event['start_date'] or dt.date.max,
                event['event_type'],
            )
        )
        venue['deadlines'] = [
            {
                **event,
                'date': event['start_date'],
            }
            for event in venue['events']
            if event['event_type'] == 'deadline' and event['start_date']
        ]
        conferences = [
            event for event in venue['events']
            if event['event_type'] == 'conference' and event['start_date']
        ]
        if conferences:
            conference = conferences[0]
            venue['conference_event'] = conference
            venue['conference'] = conference['start_date']
            venue['conference_end'] = conference['end_date'] or conference['start_date']

    return list(venues.values())


def event_needs_review(event, today=None, stale_days=180):
    """Return why an event needs verification, or an empty string if current."""
    today = today or dt.date.today()
    if event.get('status') != 'confirmed':
        return f"status is {event.get('status') or 'missing'}"
    verified_on = event.get('verified_on')
    if not verified_on:
        return 'verification date is missing'
    if (today - verified_on).days > stale_days:
        return f'verified {verified_on.isoformat()} ({(today - verified_on).days} days ago)'
    if not event.get('source_url'):
        return 'source URL is missing'
    if event.get('event_type') == 'conference' and not event.get('location'):
        return 'location is missing'
    return ''


def venue_matches_fit(venue, requested_tags):
    requested = {tag.strip().lower() for tag in requested_tags if tag.strip()}
    return not requested or bool(requested.intersection(venue.get('fit_tags', [])))


def fit_match_count(venue, requested_tags):
    requested = {tag.strip().lower() for tag in requested_tags if tag.strip()}
    return len(requested.intersection(venue.get('fit_tags', [])))


def date_span(venues):
    dates = [
        event['start_date']
        for venue in venues
        for event in venue['events']
        if event.get('start_date')
    ]
    return (min(dates), max(dates)) if dates else (None, None)
