"""Print a decision-oriented summary of HIL publication venues."""

import argparse
import csv
import datetime as dt

from venue_data import (
    VALID_SCOPES,
    event_needs_review,
    fit_match_count,
    load_venues,
    venue_matches_fit,
)


RESET = '\033[0m'
BOLD = '\033[1m'
DIM = '\033[2m'
RED = '\033[31m'
YELLOW = '\033[33m'
GREEN = '\033[32m'


def load_targets(path='targets.csv'):
    targets = {}
    try:
        with open(path, newline='', encoding='utf-8') as f:
            for row in csv.DictReader(f):
                venue = row['venue'].strip()
                targets.setdefault(venue, []).append({
                    'paper': row.get('paper', '').strip(),
                    'notes': row.get('notes', '').strip(),
                })
    except FileNotFoundError:
        pass
    return targets


def fmt_date(value):
    return value.strftime('%b %-d, %Y')


def fmt_range(start, end):
    if not end or end == start:
        return fmt_date(start)
    return f'{fmt_date(start)} – {fmt_date(end)}'


def urgency_marker(days_away):
    if days_away < 0:
        return f'{DIM}[passed]{RESET}'
    if days_away <= 30:
        return f'{RED}[in {days_away}d]{RESET}'
    if days_away <= 60:
        return f'{YELLOW}[in {days_away}d]{RESET}'
    return f'{DIM}[in {days_away}d]{RESET}'


def status_marker(event):
    if event['status'] == 'confirmed':
        return f'{GREEN}[confirmed]{RESET}'
    if event['status'] == 'tba':
        return f'{YELLOW}[TBA]{RESET}'
    return f'{YELLOW}[expected; verify]{RESET}'


def external_signals(venue):
    signals = []
    if venue.get('ccf_rank'):
        signals.append(f'CCF {venue["ccf_year"]}: {venue["ccf_rank"]}')
    if venue.get('icore_rank'):
        signals.append(f'ICORE {venue["icore_year"]}: {venue["icore_rank"]}')
    return ' | '.join(signals)


def next_sort_date(venue):
    return min((item['date'] for item in venue['deadlines']), default=dt.date.max)


def filter_venues(venues, fit_tags, needs_review=False, since=None, until=None):
    today = dt.date.today()
    venues = [venue for venue in venues if venue_matches_fit(venue, fit_tags)]

    for venue in venues:
        if since or until:
            venue['deadlines'] = [
                deadline for deadline in venue['deadlines']
                if (not since or deadline['date'] >= since)
                and (not until or deadline['date'] <= until)
            ]

    if since or until:
        venues = [venue for venue in venues if venue['deadlines']]
    if needs_review:
        venues = [
            venue for venue in venues
            if any(event_needs_review(event, today) for event in venue['events'])
        ]

    venues.sort(key=lambda venue: (
        -fit_match_count(venue, fit_tags),
        next_sort_date(venue),
        venue['name'].casefold(),
    ))
    return venues


def print_next(venues, count, targets):
    today = dt.date.today()
    upcoming = []
    for venue in venues:
        for deadline in venue['deadlines']:
            if deadline['date'] >= today:
                upcoming.append((deadline['date'], venue, deadline))
    upcoming.sort(key=lambda item: item[0])
    upcoming = upcoming[:count]

    if not upcoming:
        print(f'\n{DIM}No upcoming deadlines found.{RESET}\n')
        return

    print(f'\n{BOLD}Next {len(upcoming)} upcoming deadlines{RESET}')
    print(DIM + '─' * 88 + RESET)
    for date, venue, deadline in upcoming:
        days = (date - today).days
        target = f' {GREEN}★{RESET}' if venue['name'] in targets else ''
        accept = venue.get('acceptance_rate_5y')
        accept_text = f'  {DIM}5y accept {accept}{RESET}' if accept else ''
        note = deadline.get('notes', '').split(';', 1)[0]
        note_text = f'  {DIM}({note}){RESET}' if note and len(note) <= 24 else ''
        print(f'  {fmt_date(date):<14}  {BOLD}{venue["name"]:<14}{RESET}'
              f'{urgency_marker(days)}  {status_marker(deadline)}'
              f'{note_text}{target}{accept_text}')
    print(f'\n{DIM}★ = targeted in targets.csv{RESET}\n')


def print_report(venues, targets, scope='core', fit_tags=(), needs_review=False,
                 since=None, until=None):
    today = dt.date.today()
    qualifiers = [f'{scope} scope']
    if fit_tags:
        qualifiers.append('fit: ' + ', '.join(fit_tags))
    if needs_review:
        qualifiers.append('needs review')
    if since:
        qualifiers.append(f'from {since}')
    if until:
        qualifiers.append(f'until {until}')
    header = f'Venue Report [{"; ".join(qualifiers)}]'
    print(f'\n{BOLD}{header}{RESET}')
    print(BOLD + '=' * len(header) + RESET)
    print(f'{DIM}today: {fmt_date(today)} | expected dates are planning aids only{RESET}\n')

    if not venues:
        print(f'{DIM}No matching venues found.{RESET}\n')
        return

    for venue in venues:
        scope_label = venue['lab_scope'].upper()
        type_label = venue['venue_type'].upper()
        print(f'{BOLD}[{scope_label} / {type_label}] {venue["name"]}{RESET}'
              f' — {venue["full_name"]}')
        print(f'  Why:         {venue["lab_fit_notes"]}')
        print(f'  Fit tags:    {", ".join(venue["fit_tags"])}')

        signals = external_signals(venue)
        if signals:
            print(f'  External:    {signals}')
        if venue.get('acceptance_rate_5y'):
            print(f'  Selectivity: {venue["acceptance_rate_5y"]} mean acceptance '
                  f'({venue["acceptance_rate_window"]}; checked '
                  f'{venue["acceptance_rate_checked"]})')

        for deadline in sorted(venue['deadlines'], key=lambda item: item['date']):
            days = (deadline['date'] - today).days
            note = deadline.get('notes', '')
            note_text = f' — {note}' if note else ''
            print(f'  Deadline:    {fmt_date(deadline["date"])}  '
                  f'{urgency_marker(days)} {status_marker(deadline)}{note_text}')
            reason = event_needs_review(deadline, today)
            if needs_review and reason:
                print(f'               {YELLOW}review: {reason}{RESET}')

        conference = venue.get('conference_event')
        if conference:
            days = (conference['start_date'] - today).days
            location = f' | {conference["location"]}' if conference['location'] else ''
            print(f'  Event:       {fmt_range(conference["start_date"], conference["end_date"])}  '
                  f'{urgency_marker(days)} {status_marker(conference)}{location}')
            reason = event_needs_review(conference, today)
            if needs_review and reason:
                print(f'               {YELLOW}review: {reason}{RESET}')
        elif venue['submission_cycle'] == 'rolling':
            relation = f'; presented at {venue["presented_at"]}' if venue['presented_at'] else ''
            print(f'  Submission:  rolling{relation}')
        else:
            print(f'  Schedule:    {DIM}no edition events tracked yet{RESET}')

        print(f'  URL:         {venue["url"]}')
        if venue.get('notes_file'):
            print(f'  Details:     {venue["notes_file"]}')
        if venue.get('ranking_notes'):
            print(f'  Rank note:   {venue["ranking_notes"]}')

        for target in targets.get(venue['name'], []):
            line = f'  {GREEN}>> Targeting:{RESET} {BOLD}{target["paper"]}{RESET}'
            if target['notes']:
                line += f' — {target["notes"]}'
            print(line)
        print()


def parse_date(value):
    try:
        return dt.date.fromisoformat(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError(
            f'Invalid date "{value}" — use YYYY-MM-DD.') from exc


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Show deadlines and lab-specific venue-selection context.')
    parser.add_argument('--scope', choices=(*VALID_SCOPES, 'all'), default='core')
    parser.add_argument('--show-all', action='store_true',
                        help='Compatibility alias for --scope all.')
    parser.add_argument('--fit', metavar='TAG[,TAG]',
                        help='Keep venues matching at least one research-fit tag.')
    parser.add_argument('--needs-review', action='store_true',
                        help='Only venues with stale, expected, TBA, or incomplete events.')
    parser.add_argument('--approx', action='store_true',
                        help='Compatibility alias for --needs-review.')
    parser.add_argument('--next', metavar='N', type=int)
    parser.add_argument('--since', metavar='YYYY-MM-DD', type=parse_date)
    parser.add_argument('--until', metavar='YYYY-MM-DD', type=parse_date)
    parser.add_argument('--venues', default='venues.csv')
    parser.add_argument('--events', default='events.csv')
    parser.add_argument('--targets', default='targets.csv')
    args = parser.parse_args()

    chosen_scope = 'all' if args.show_all else args.scope
    requested_tags = [tag.strip() for tag in (args.fit or '').split(',') if tag.strip()]
    review_only = args.needs_review or args.approx
    loaded = load_venues(args.venues, args.events, scope=chosen_scope)
    loaded = filter_venues(loaded, requested_tags, review_only,
                           since=args.since, until=args.until)
    loaded_targets = load_targets(args.targets)

    if args.next:
        print_next(loaded, args.next, loaded_targets)
    else:
        print_report(loaded, loaded_targets, scope=chosen_scope,
                     fit_tags=requested_tags, needs_review=review_only,
                     since=args.since, until=args.until)
