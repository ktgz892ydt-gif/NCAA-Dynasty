"""Regression checks for the audited data and coverage boundaries."""
import copy
import json
import unittest
from reconcile_2026 import ROOT, read_site, reconcile


class ReconciliationTests(unittest.TestCase):
    def setUp(self):
        self.data = read_site(ROOT / 'index.html')[3]
        self.source = json.loads((ROOT / 'data/verified-inputs-2026.json').read_text())
        self.result = reconcile(copy.deepcopy(self.data), self.source)

    def test_scoreboard_and_ratings_preserved(self):
        self.assertEqual(len(self.result['scoreboard']), 888)
        self.assertEqual(len(self.result['ratings']), 143)
        for key in ['scoreboard', 'ratings', 'schedules', 'playerLeaders', 'nationalLeaders', 'params']:
            self.assertEqual(self.result[key], self.data[key])

    def test_full_season_offense_recomputed_together(self):
        expected = {'W. Michigan': 127.14685446750124, 'E. Michigan': 68.22219114520021,
                    'C. Michigan': 104.63095438729859}
        for team, amount in expected.items():
            v = self.result['values'][team]
            self.assertAlmostEqual(v['av_team_off']['v'], amount)
            self.assertAlmostEqual(v['av_oline_pool']['v'] + v['av_skill_pool']['v'], amount)
            self.assertAlmostEqual(sum(v[k]['v'] for k in ['av_rush_pool', 'av_pass_pool', 'av_rec_pool']),
                                   v['av_skill_pool']['v'])
        self.assertAlmostEqual(self.result['avNotes']['Eastern Michigan']['off_pts_per_drive'], 1.408)

    def test_one_drive_definition_for_offense_and_defense(self):
        """Possessions alternate, so a defence faces its own offence's drive count."""
        notes = self.result['avNotes']
        for team in self.result['teams']:
            n = notes[self.result['full'][team]]
            self.assertEqual(n['drives'], n['def_drives'])
            # a real college team gets roughly twelve possessions a game
            self.assertTrue(10 <= n['drives'] / 12 <= 13, n['drives'] / 12)
            # Explosiveness must use that same count, not a second definition
            v = self.result['values'][team]
            self.assertAlmostEqual(v['explo']['v'], v['ypp']['v'] * v['pts']['v'] / n['drives'])

    def test_defense_no_longer_depends_on_estimated_opponent_field_goals(self):
        notes = self.result['avNotes']
        for team in self.result['teams']:
            self.assertNotIn('opp_fga', notes['inputs'][self.result['full'][team]])
        # ranking must agree with points allowed per drive, best defence first
        by_av = sorted(self.result['teams'],
                       key=lambda t: -self.result['values'][t]['av_team_def']['v'])
        by_rate = sorted(self.result['teams'],
                         key=lambda t: notes['inputs'][self.result['full'][t]]['pts_allowed']
                         / notes[self.result['full'][t]]['def_drives'])
        self.assertEqual(by_av, by_rate)
        for team in self.result['teams']:
            v = self.result['values'][team]
            self.assertAlmostEqual(v['av_front7_pool']['v'], v['av_team_def']['v'] * 2 / 3)
            self.assertAlmostEqual(v['av_secondary_pool']['v'], v['av_team_def']['v'] / 3)

    def test_partial_punt_average_does_not_use_season_count(self):
        v = self.result['values']['E. Michigan']
        self.assertEqual(v['punts']['v'], 25)
        self.assertEqual(v['kr']['v'], 937)
        self.assertEqual(v['pr']['v'], 269)
        self.assertAlmostEqual(v['ypunt']['v'], 969 / 21)
        self.assertEqual(v['ypunt']['partial'], 11)
        self.assertEqual(v['puntyds']['partial'], 11)
        self.assertNotIn('partial', v['punts'])
        self.assertAlmostEqual(v['toppg']['v'], 976.25)
        self.assertAlmostEqual(v['bci']['v'], .5 * (11715 / 25920) + .3 * (173 / 567) - .2 * (31 / 567))
        self.assertAlmostEqual(v['explo']['v'], 8.512)

    def test_exact_punter_totals(self):
        for team, yards, count in [('W. Michigan', 1121, 26), ('C. Michigan', 1623, 36)]:
            v = self.result['values'][team]
            self.assertEqual(v['puntyds']['v'], yards)
            self.assertAlmostEqual(v['ypunt']['v'], yards / count)

    def test_unsupported_player_results_stay_missing(self):
        for team in self.result['teams']:
            for pos in ['LT', 'LG', 'C', 'RG', 'RT']:
                self.assertIsNone(self.result['values'][team]['av_ol_' + pos]['v'])
        self.assertIsNone(self.result['values']['E. Michigan']['av_punter']['v'])

    def test_estimate_caveat_propagates_to_shared_defense_baseline(self):
        for team in self.result['teams']:
            for key in ['av_team_def', 'av_front7_pool', 'av_secondary_pool']:
                cell = self.result['values'][team][key]
                self.assertTrue(cell['estimate'])
                self.assertIn('possessions alternate', cell['note'])
        self.assertIn('20 takeaways', self.result['values']['C. Michigan']['todiff']['note'])

    def test_user_entered_results_come_from_the_source_file(self):
        values = self.result['values']
        self.assertEqual(values['C. Michigan']['confchamp']['v'], 'Yes')
        for team in ['W. Michigan', 'E. Michigan']:
            self.assertEqual(values[team]['confchamp']['v'], 'No')
        for team, result in [('W. Michigan', 'Win'), ('E. Michigan', 'N/A'),
                             ('C. Michigan', 'Win')]:
            self.assertEqual(values[team]['bowl']['v'], result)
        # not supplied yet, and nothing in the source set records them
        for team in self.result['teams']:
            self.assertIsNone(values[team]['cfp']['v'])

    def test_repeat_build_is_stable(self):
        self.assertEqual(reconcile(copy.deepcopy(self.result), self.source), self.result)

    def test_changed_punt_input_updates_every_offensive_pool(self):
        changed = copy.deepcopy(self.source)
        changed['eastern_first_game']['punts'] += 1
        alternate = reconcile(copy.deepcopy(self.data), changed)
        for team in self.result['teams']:
            self.assertNotEqual(alternate['values'][team]['av_team_off']['v'],
                                self.result['values'][team]['av_team_off']['v'])
        self.assertEqual(alternate['values']['E. Michigan']['ypunt'],
                         self.result['values']['E. Michigan']['ypunt'])


if __name__ == '__main__':
    unittest.main()
