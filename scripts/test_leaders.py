"""Checks on the transcribed national player leaderboards."""
import copy
import json
import unittest
from reconcile_2026 import ROOT, read_site
from update_leaders import check_identities, load_sources, apply


class LeaderTests(unittest.TestCase):
    def setUp(self):
        self.data = read_site(ROOT / 'index.html')[3]
        self.sources = {s['category']: s for s in load_sources()}
        self.leaders = self.data['playerLeaders']

    def test_transcribed_categories_are_as_deep_as_their_source(self):
        for category, source in self.sources.items():
            self.assertEqual(len(self.leaders[category]['rows']), len(source['rows']), category)

    def test_identities_hold_on_every_row(self):
        for source in self.sources.values():
            check_identities(source)

    def test_a_broken_row_is_rejected(self):
        for category, source in self.sources.items():
            broken = copy.deepcopy(source)
            v = broken['rows'][len(broken['rows']) // 2]['values']
            v[source['sortedBy']] = v[source['sortedBy']] + 1000   # breaks the sort
            with self.assertRaises(ValueError, msg=category):
                check_identities(broken)

    def test_completeness_is_recorded_and_honest(self):
        complete = self.data['leaderComplete']
        self.assertTrue(complete['DEFENSE'])
        self.assertTrue(complete['KICK RETURN'])
        # only two stills exist for punt returns, so it stops short of the list's end
        self.assertFalse(complete['PUNT RETURN'])
        # categories with no transcription file are not complete either
        for category in self.leaders:
            if category not in self.sources:
                self.assertFalse(complete[category], category)

    def test_depth_matches_the_rendered_rows(self):
        for category, block in self.leaders.items():
            self.assertEqual(self.data['leaderDepth'][category], len(block['rows']), category)

    def test_known_endpoints(self):
        self.assertEqual(self.leaders['DEFENSE']['rows'][-1]['name'], 'M.Malaki-Donaldson')
        self.assertEqual(self.leaders['KICK RETURN']['rows'][0]['name'], 'R.Kidd')
        self.assertEqual(self.leaders['KICK RETURN']['rows'][-1]['name'], 'L.Burrell')
        self.assertEqual(self.leaders['PUNT RETURN']['rows'][0]['name'], 'J.Ruffin Jr.')

    def test_teams_are_not_guessed(self):
        for category, block in self.leaders.items():
            if category in self.sources:
                for row in block['rows']:
                    self.assertIn(row['team'], (None, 'Buffalo', 'New Mexico'), category)

    def test_repeat_apply_is_stable(self):
        once = apply(copy.deepcopy(self.data), list(self.sources.values()))
        twice = apply(copy.deepcopy(once), list(self.sources.values()))
        self.assertEqual(once, twice)

    def test_columns_must_match_data(self):
        bad = copy.deepcopy(self.sources['KICK RETURN'])
        bad['columns'] = bad['columns'][:-1]
        with self.assertRaises(ValueError):
            apply(copy.deepcopy(self.data), [bad])


if __name__ == '__main__':
    unittest.main()
