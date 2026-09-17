"""Checks on the opponent-adjusted offensive and defensive ratings."""
import copy
import json
import unittest
from reconcile_2026 import ROOT, read_site
from update_efficiency import observations, solve, residual_rmse, update_efficiency


class EfficiencyTests(unittest.TestCase):
    def setUp(self):
        self.data = read_site(ROOT / 'index.html')[3]
        self.teams = [r['t'] for r in self.data['ratings']]
        self.hfa = self.data['params']['estimated_home_field_advantage']

    def test_margin_reproduces_the_published_srs(self):
        """The decomposition is solved from scratch; SRS came from the ratings export.

        Two different methods over the same games: alternating least squares here,
        a direct least-squares solve there. They have to agree, and at the two
        decimals the site stores they agree exactly for every team.
        """
        for row in self.data['ratings']:
            self.assertEqual(round(row['adjo'] - row['adjd'], 2), row['srs'], row['t'])

    def test_full_precision_margin_matches_the_ratings_export(self):
        published = json.loads((ROOT / 'data/srs-2026.json').read_text())['ratings']
        self.assertEqual(len(published), len(self.data['ratings']))
        worst = max(abs((r['adjo'] - r['adjd']) - published[r['t']]) for r in self.data['ratings'])
        self.assertLess(worst, 1e-6, f'largest gap to the ratings export: {worst}')

    def test_both_halves_average_the_league_mean(self):
        """Offence and defence are centred, so each averages the league's points per game."""
        mean = self.data['effMethod']['league_average_points_per_game']
        for key in ['adjo', 'adjd']:
            values = [r[key] for r in self.data['ratings']]
            self.assertAlmostEqual(sum(values) / len(values), mean, places=9)
        margins = [r['adjem'] for r in self.data['ratings']]
        self.assertAlmostEqual(sum(margins) / len(margins), 0.0, places=9)

    def test_the_solve_actually_converged(self):
        rows = observations(self.data)
        self.assertEqual(len(rows), 2 * len(self.data['scoreboard']))
        mu, off, deff, sweeps = solve(rows, self.teams, self.hfa)
        self.assertLess(sweeps, 1000)
        # a fitted points-per-game model should land inside a converted touchdown
        self.assertLess(residual_rmse(rows, self.teams, mu, off, deff, self.hfa), 12)

    def test_ranks_cover_only_the_real_fbs_teams(self):
        eligible = [r['t'] for r in self.data['ratings'] if not r['syn']]
        for key in ['adjo', 'adjd', 'adjem']:
            for short in self.data['teams']:
                cell = self.data['values'][short][key]
                self.assertEqual(cell['of'], len(eligible))
                self.assertTrue(1 <= cell['rank'] <= len(eligible))
        # the better defence takes the lower rank
        best = min(eligible, key=lambda t: next(r['adjd'] for r in self.data['ratings'] if r['t'] == t))
        self.assertEqual(self.data['nationalLeaders']['adjd'][0]['t'], best)

    def test_only_the_two_halves_are_surfaced(self):
        """AdjO - AdjD is exactly SRS, so a margin row would print one number twice."""
        order = [m['key'] for m in self.data['statMeta']]
        self.assertEqual(order[order.index('mov') + 1:order.index('mov') + 3], ['adjo', 'adjd'])
        self.assertNotIn('adjem', order)
        self.assertNotIn('adjem', self.data['nationalLeaders'])
        # it survives where the SRS agreement is checked, just not as a statistic
        for row in self.data['ratings']:
            self.assertIn('adjem', row)
        page = (ROOT / 'index.html').read_text()
        block = page[page.index("[['pyth'"):page.index(']].forEach')]
        self.assertIn("['adjo'", block)
        self.assertIn("['adjd'", block)
        self.assertNotIn("['adjem'", block)

    def test_repeat_run_is_stable(self):
        once = update_efficiency(copy.deepcopy(self.data))
        twice = update_efficiency(copy.deepcopy(once))
        self.assertEqual(once, twice)


if __name__ == '__main__':
    unittest.main()
