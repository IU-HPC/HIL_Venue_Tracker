"""Export tracked venue deadlines and event ranges to iCalendar."""

import argparse
import datetime as dt

from venue_data import VALID_SCOPES, load_venues


DEADLINE_REMINDER_DAYS = 30


def ical_escape(value):
    return (value or '').replace('\\', '\\\\').replace('\n', '\\n').replace(',', '\\,').replace(';', '\\;')


def fold(line):
    """Fold a content line at 75 UTF-8 octets without splitting characters."""
    if len(line.encode('utf-8')) <= 75:
        return line
    chunks = []
    current = ''
    for char in line:
        candidate = current + char
        limit = 75 if not chunks else 74
        if len(candidate.encode('utf-8')) > limit:
            chunks.append(current)
            current = char
        else:
            current = candidate
    chunks.append(current)
    return '\r\n '.join(chunks)


def fmt_date(value):
    return value.strftime('%Y%m%d')


def make_uid(name, event_type, edition, date):
    safe = name.replace(' ', '-').replace('/', '-').lower()
    return f'{safe}-{edition}-{event_type}-{fmt_date(date)}@hil-venue-tracker'


def short_note(event):
    note = event.get('notes', '').split(';', 1)[0].strip()
    if note.lower().startswith(('date carried forward', 'approximate date')):
        return ''
    return note


def vevent(summary, start, end, description, url, uid, location='', reminder_days=None):
    lines = [
        'BEGIN:VEVENT',
        f'UID:{uid}',
        f'DTSTART;VALUE=DATE:{fmt_date(start)}',
        f'DTEND;VALUE=DATE:{fmt_date(end + dt.timedelta(days=1))}',
        fold(f'SUMMARY:{ical_escape(summary)}'),
        fold(f'DESCRIPTION:{ical_escape(description)}'),
    ]
    if location:
        lines.append(fold(f'LOCATION:{ical_escape(location)}'))
    if url:
        lines.append(fold(f'URL:{url}'))
    if reminder_days:
        lines += [
            'BEGIN:VALARM',
            f'TRIGGER:-P{reminder_days}D',
            'ACTION:DISPLAY',
            fold(f'DESCRIPTION:{ical_escape("Reminder: " + summary)}'),
            'END:VALARM',
        ]
    lines.append('END:VEVENT')
    return lines


def generate_ical(venues, output_path='deadlines.ics', scope='core'):
    lines = [
        'BEGIN:VCALENDAR',
        'VERSION:2.0',
        'PRODID:-//HIL Venue Tracker//EN',
        'CALSCALE:GREGORIAN',
        'METHOD:PUBLISH',
        f'X-WR-CALNAME:HIL Venue Deadlines ({scope})',
        'X-WR-CALDESC:Lab-focused publication deadlines and venue dates',
    ]
    deadline_count = 0
    venue_count = 0

    for venue in venues:
        for deadline in venue['deadlines']:
            status = '' if deadline['status'] == 'confirmed' else ' [EXPECTED]'
            brief = short_note(deadline)
            note = f' ({brief})' if brief else ''
            summary = f'{venue["name"]} Paper Deadline{note}{status}'
            description = (
                f'{venue["full_name"]} submission deadline. '
                f'Status: {deadline["status"]}. Source: {deadline["source_url"]}'
            )
            lines += vevent(
                summary, deadline['date'], deadline['date'], description,
                deadline['source_url'] or venue['url'],
                make_uid(venue['name'], 'deadline', deadline['edition'], deadline['date']),
                reminder_days=DEADLINE_REMINDER_DAYS,
            )
            deadline_count += 1

        event = venue.get('conference_event')
        if event:
            status = '' if event['status'] == 'confirmed' else ' [EXPECTED]'
            summary = f'{venue["name"]} {venue["venue_type"].title()}{status}'
            description = (
                f'{venue["full_name"]}. Status: {event["status"]}. '
                f'Source: {event["source_url"]}'
            )
            lines += vevent(
                summary, event['start_date'], event['end_date'] or event['start_date'],
                description, event['source_url'] or venue['url'],
                make_uid(venue['name'], 'event', event['edition'], event['start_date']),
                location=event['location'],
            )
            venue_count += 1

    lines.append('END:VCALENDAR')
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        f.write('\r\n'.join(lines) + '\r\n')

    print(f'Saved to {output_path}')
    print(f'  {deadline_count} deadline events ({DEADLINE_REMINDER_DAYS}-day reminders)')
    print(f'  {venue_count} venue date events')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Export HIL venue dates to iCalendar.')
    parser.add_argument('--scope', choices=(*VALID_SCOPES, 'all'), default='core')
    parser.add_argument('--show-all', action='store_true',
                        help='Compatibility alias for --scope all.')
    parser.add_argument('--venues', default='venues.csv')
    parser.add_argument('--events', default='events.csv')
    parser.add_argument('--output', default='deadlines.ics')
    args = parser.parse_args()

    chosen_scope = 'all' if args.show_all else args.scope
    loaded = load_venues(args.venues, args.events, scope=chosen_scope)
    generate_ical(loaded, output_path=args.output, scope=chosen_scope)
