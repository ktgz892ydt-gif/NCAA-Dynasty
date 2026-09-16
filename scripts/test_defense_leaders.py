"""Checks on the full national DEFENSE leaderboard transcription."""
import json
import unittest
from reconcile_2026 import ROOT, read_site
from update_defense_leaders import check_invariants


class DefenseLeaderTests(unittest.TestCase):
    def setUp(self):
        self.data = read_site(ROOT / 'index.html')[3]
        self.source = json.loads((ROOT / 'data/defense-leaders-2026.json').read_text())
        self.rows = self.data['playerLeaders']['DEFENSE']['rows']

    def test_whole_list_is_present(self):
        """The recording scrolls to the bottom; the leaderboard holds 400 players."""
        self.assertEqual(len(self.rows), 400)
        self.assertEqual(len(self.source['rows']), 400)
        self.assertEqual(self.rows[0]['name'], 'S.Bracey')
        self.assertEqual(self.rows[-1]['name'], 'M.Malaki-Donaldson')
        self.assertEqual(self.rows[0]['values']['TAK'], 124)
        self.assertEqual(self.rows[-1]['values']['TAK'], 57)

    def test_arithmetic_identities_hold_on_every_row(self):
        check_invariants(self.rows)

    def test_a_broken_row_is_rejected(self):
        broken = json.loads(json.dumps(self.rows))
        broken[100]['values']['ASSISTS'] += 1
        with self.assertRaises(ValueError):
            check_invariants(broken)

    def test_sort_order_is_enforced(self):
        broken = json.loads(json.dumps(self.rows))
        broken[50], broken[300] = broken[300], broken[50]
        with self.assertRaises(ValueError):
            check_invariants(broken)

    def test_teams_are_not_guessed(self):
        """The screen prints no team column, so only highlighted players are known."""
        named = {r['name']: r['team'] for r in self.rows if r['team']}
        self.assertEqual(named, {'S.Bracey': 'Buffalo', 'J.Eck': 'New Mexico'})

    def test_tackles_for_loss_is_present_but_cannot_give_a_team_total(self):
        """TFL is on this screen; it is the roster coverage that is missing."""
        self.assertIn('TFL', self.data['playerLeaders']['DEFENSE']['columns'])
        self.assertTrue(any(r['values']['TFL'] for r in self.rows))
        # every dynasty team's TFL row stays blank
        for team in self.data['teams']:
            self.assertIsNone(self.data['values'][team]['tfl']['v'])

    def test_depth_is_recorded_for_the_page(self):
        depth = self.data['leaderDepth']
        self.assertEqual(depth['DEFENSE'], 400)
        # the other categories are still a single screenful from the earlier pass
        for key, count in depth.items():
            if key != 'DEFENSE':
                self.assertLess(count, 40, key)


if __name__ == '__main__':
    unittest.main()
