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

    def test_teams_come_only_from_the_source_files(self):
        """No team label may be invented in the site; the screens print no team column."""
        for category, source in self.sources.items():
            declared = {(r['name'], r['team']) for r in source['rows'] if r['team']}
            live = {(r['name'], r['team']) for r in self.leaders[category]['rows'] if r['team']}
            self.assertEqual(live, declared, category)
            # a transcribed category should carry only a handful of attributions
            self.assertLessEqual(len(live), 5, category)

    def test_the_three_punters_are_identified_by_a_unique_punt_count(self):
        """The complete 138-punter field is what makes the attribution safe."""
        rows = self.leaders['PUNTING']['rows']
        self.assertEqual(len(rows), 138)
        by_team = {r['team']: r for r in rows if r['team']}
        self.assertEqual(set(by_team), {'Western Michigan', 'Eastern Michigan', 'Central Michigan'})
        for team, punts in [('Central Michigan', 36), ('Western Michigan', 26),
                            ('Eastern Michigan', 25)]:
            self.assertEqual(by_team[team]['values']['PUNTS'], punts)
            # exactly one punter in the whole country has that count
            self.assertEqual(sum(r['values']['PUNTS'] == punts for r in rows), 1, team)
        # and they agree with the season inputs the site computes from
        source = json.loads((ROOT / 'data/verified-inputs-2026.json').read_text())
        for short, full in [('W. Michigan', 'Western Michigan'),
                            ('E. Michigan', 'Eastern Michigan'),
                            ('C. Michigan', 'Central Michigan')]:
            entered = source['punters'][short]
            self.assertEqual(entered['name'], by_team[full]['name'])
            self.assertEqual(entered['punts'], by_team[full]['values']['PUNTS'])
            self.assertEqual(entered['yards'], by_team[full]['values']['YARDS'])
            self.assertEqual(entered['blocked'], by_team[full]['values']['BLOCK'])

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
