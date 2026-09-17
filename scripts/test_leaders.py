"""Checks on the transcribed national player leaderboards."""
import copy
import json
import unittest
from season_io import ROOT
from update_leaders import check_identities, load_sources, apply


class LeaderTests(unittest.TestCase):
    def setUp(self):
        self.data = json.loads((ROOT / 'data/seasons/2026/season.json').read_text())
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
        source = json.loads((ROOT / 'data/seasons/2026/inputs/verified-corrections.json').read_text())
        for short, full in [('W. Michigan', 'Western Michigan'),
                            ('E. Michigan', 'Eastern Michigan'),
                            ('C. Michigan', 'Central Michigan')]:
            entered = source['punters'][short]
            self.assertEqual(entered['name'], by_team[full]['name'])
            self.assertEqual(entered['punts'], by_team[full]['values']['PUNTS'])
            self.assertEqual(entered['yards'], by_team[full]['values']['YARDS'])
            self.assertEqual(entered['blocked'], by_team[full]['values']['BLOCK'])

    def test_snaps_agree_across_categories(self):
        """A player's snap count is one number, however many leaderboards he reaches.

        This is the strongest check available on the columns the screens derive
        nothing from: the categories were transcribed independently, so agreement
        is evidence about both. The exceptions are not errors - the game prints
        an initial and a surname, so a handful of name-and-position keys cover
        two different players.
        """
        from collections import defaultdict
        per = defaultdict(lambda: defaultdict(set))
        for category, block in self.leaders.items():
            if 'SNAPS' not in block['columns']:
                continue
            for row in block['rows']:
                per[(row['name'], row['pos'])][category].add(row['values']['SNAPS'])
        shared = {k: v for k, v in per.items() if len(v) > 1}
        self.assertGreater(len(shared), 150)
        consistent = [k for k, v in shared.items() if set.intersection(*v.values())]
        self.assertGreater(len(consistent) / len(shared), 0.9)

    def test_dual_returners_agree_between_the_two_return_lists(self):
        kr = {(r['name'], r['pos']): r['values']['SNAPS']
              for r in self.leaders['KICK RETURN']['rows']}
        pr = {(r['name'], r['pos']): r['values']['SNAPS']
              for r in self.leaders['PUNT RETURN']['rows']}
        both = set(kr) & set(pr)
        self.assertGreater(len(both), 5)
        for key in both:
            self.assertEqual(kr[key], pr[key], key)

    def test_air_yards_are_derived_and_marked_as_such(self):
        """Air yards are worked out, not read, so they must be flagged and must add up."""
        block = self.leaders['RECEIVING']
        self.assertEqual(block['derived'], ['AIR YDS', 'AIR/REC'])
        for name in block['derived']:
            self.assertIn(name, block['columns'])
            self.assertNotIn(name, self.sources['RECEIVING']['columns'])
        for row in block['rows']:
            v = row['values']
            self.assertEqual(v['AIR YDS'] + v['RAC'], v['YARDS'], row['name'])
            self.assertGreaterEqual(v['AIR YDS'], 0)
            self.assertAlmostEqual(v['AIR/REC'], round(v['AIR YDS'] / v['REC'], 1), places=9)
        # a running back catching checkdowns must sit below a deep receiver
        depth = {r['name']: r['values']['AIR/REC'] for r in block['rows']}
        self.assertLess(depth['J.Buckley'], depth['C.Moss'])

    def test_no_other_category_gains_derived_columns(self):
        for category, block in self.leaders.items():
            if category != 'RECEIVING':
                self.assertNotIn('derived', block, category)
                if category in self.sources:
                    self.assertEqual(block['columns'], self.sources[category]['columns'])

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
