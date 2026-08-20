import tempfile
import unittest
from pathlib import Path

from generate_ical import generate_ical
from report import filter_venues
from timeline_generator import venue_label
from validate_data import validate
from venue_data import load_venues


ROOT = Path(__file__).resolve().parents[1]
VENUES = ROOT / 'venues.csv'
EVENTS = ROOT / 'events.csv'


class TrackerDataTests(unittest.TestCase):
    def test_schema_and_references_validate(self):
        errors, warnings, venue_count, event_count = validate(VENUES, EVENTS)
        self.assertEqual(errors, [])
        self.assertGreater(len(warnings), 0)
        self.assertEqual(venue_count, 36)
        self.assertEqual(event_count, 47)

    def test_default_scope_and_journal_model(self):
        core = load_venues(VENUES, EVENTS)
        self.assertTrue(core)
        self.assertTrue(all(venue['lab_scope'] == 'core' for venue in core))
        taco = next(venue for venue in core if venue['name'] == 'TACO')
        self.assertEqual(taco['venue_type'], 'journal')
        self.assertEqual(taco['submission_cycle'], 'rolling')
        self.assertIsNone(taco['conference'])

    def test_fit_filter_finds_watch_candidates(self):
        watch = load_venues(VENUES, EVENTS, scope='watch')
        matches = filter_venues(watch, ['data-reduction'])
        self.assertEqual(
            {venue['name'] for venue in matches},
            {'DCC', 'FAST', 'IEEE VIS'},
        )

    def test_fz_recommendations_have_expected_scopes(self):
        venues = {venue['name']: venue for venue in load_venues(VENUES, EVENTS, scope='all')}
        self.assertEqual(venues['CLUSTER']['lab_scope'], 'adjacent')
        self.assertEqual(venues['HiPC']['lab_scope'], 'adjacent')
        self.assertEqual(venues['IEEE BigData']['lab_scope'], 'adjacent')
        self.assertEqual(venues['IWBDR']['venue_type'], 'workshop')
        self.assertEqual(venues['MASCOTS']['lab_scope'], 'watch')
        self.assertEqual(venues['IEEE VIS']['lab_scope'], 'watch')
        self.assertEqual(venues['ISC']['lab_scope'], 'watch')
        self.assertEqual(venues['TPDS']['submission_cycle'], 'rolling')

    def test_timeline_label_shows_external_ranks(self):
        sc = next(venue for venue in load_venues(VENUES, EVENTS) if venue['name'] == 'SC')
        self.assertEqual(venue_label(sc), 'SC  [CCF A · ICORE A]')

    def test_calendar_marks_expected_dates(self):
        core = load_venues(VENUES, EVENTS)
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / 'deadlines.ics'
            generate_ical(core, output, scope='core')
            data = output.read_bytes()
        self.assertTrue(data.startswith(b'BEGIN:VCALENDAR\r\n'))
        self.assertIn(b'[EXPECTED]', data)
        self.assertTrue(data.endswith(b'END:VCALENDAR\r\n'))
        self.assertLessEqual(max(map(len, data.split(b'\r\n'))), 75)


if __name__ == '__main__':
    unittest.main()
