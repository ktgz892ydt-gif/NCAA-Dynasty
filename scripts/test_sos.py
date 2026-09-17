import copy
import json
import unittest
from update_sos import ROOT, opponent_averages, update_sos


class SOSTests(unittest.TestCase):
    def setUp(self):
        self.data = json.loads((ROOT / 'data/seasons/2026/season.json').read_text())
        self.source = json.loads((ROOT / 'data/seasons/2026/inputs/srs-reference.json').read_text())

    def test_each_game_counts_including_repeat_opponents(self):
        games = [{'a':'A','h':'B'}, {'a':'A','h':'B'}, {'a':'A','h':'C'}]
        scores = opponent_averages(games, {'A':0, 'B':6, 'C':-3})
        self.assertEqual(scores, {'A':3, 'B':0, 'C':0})

    def test_missing_rating_is_rejected(self):
        with self.assertRaises(ValueError):
            opponent_averages([{'a':'A','h':'Missing'}], {'A':0})

    def test_new_scoreboard_requires_fresh_srs(self):
        d = copy.deepcopy(self.data)
        d['scoreboard'][0]['as'] += 1
        with self.assertRaises(ValueError):
            update_sos(d, self.source)

    def test_srs_equals_adjusted_margin_plus_sos_for_all_teams(self):
        d = update_sos(copy.deepcopy(self.data), self.source)
        margins = {t: [] for t in self.source['ratings']}
        hfa = d['params']['estimated_home_field_advantage']
        for game in d['scoreboard']:
            margin = game['as'] - game['hs'] + (0 if game['n'] else hfa)
            margins[game['a']].append(margin)
            margins[game['h']].append(-margin)
        for row in d['ratings']:
            team = row['t']
            self.assertAlmostEqual(self.source['ratings'][team],
                sum(margins[team]) / len(margins[team]) + row['sos'], places=8)

    def test_fbs_ranking_and_unrelated_data_preserved(self):
        d = update_sos(copy.deepcopy(self.data), self.source)
        eligible = [r for r in d['ratings'] if not r['syn']]
        self.assertEqual(len(eligible), 138)
        for team in d['teams']:
            cell = d['values'][team]['sos']
            self.assertEqual(cell['of'], 138)
            self.assertEqual(cell['rank'], 1 + sum(r['sos'] > cell['v'] for r in eligible))
            for key in self.data['values'][team]:
                if key != 'sos':
                    self.assertEqual(d['values'][team][key], self.data['values'][team][key])
        for key in ['scoreboard', 'schedules', 'playerLeaders', 'avNotes', 'params']:
            self.assertEqual(d[key], self.data[key])
        self.assertTrue(all(not next(r['syn'] for r in d['ratings'] if r['t']==leader['t'])
                            for leader in d['nationalLeaders']['sos']))
        self.assertEqual(update_sos(copy.deepcopy(d), self.source), d)


if __name__ == '__main__':
    unittest.main()
