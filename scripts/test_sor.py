import copy
import itertools
import json
import math
import unittest
from update_sor import ROOT, fit_slope, logistic, record_tail, update_sor


class SORTests(unittest.TestCase):
    def test_exact_probability_against_enumeration(self):
        ps = [.2,.5,.8,.95]
        for wins in range(5):
            expected = sum(math.prod(p if won else 1-p for p,won in zip(ps,result))
                           for result in itertools.product([0,1],repeat=4) if sum(result)>=wins)
            self.assertAlmostEqual(record_tail(ps,wins),expected,places=14)
        self.assertEqual(record_tail([0,1],1),1)
        self.assertEqual(record_tail([0,1],2),0)
        self.assertEqual(record_tail([],0),1)

    def test_better_records_and_harder_schedules(self):
        self.assertLess(record_tail([.7]*12,10),record_tail([.7]*12,9))
        self.assertLess(record_tail([.6]*12,9),record_tail([.8]*12,9))
        self.assertAlmostEqual(logistic(0),.5)
        self.assertAlmostEqual(logistic(.6)+logistic(-.6),1)

    def test_fit_known_odds(self):
        beta=fit_slope([(1,1)]*3+[(1,0)])
        self.assertAlmostEqual(beta,math.log(3),places=12)

    def test_full_field_and_preservation(self):
        before=json.loads((ROOT / 'data/seasons/2026/season.json').read_text())
        source=json.loads((ROOT/'data/seasons/2026/inputs/srs-reference.json').read_text())
        d=update_sor(copy.deepcopy(before),source)
        self.assertEqual(update_sor(copy.deepcopy(d),source),d)
        method=d['sorMethod']; self.assertEqual(len(method['teams']),138)
        self.assertLess(method['week_held_out_slope_brier'],.25)
        self.assertTrue(all(0<=t['match_probability']<=1 for t in method['teams'].values()))
        for row in d['ratings']:
            if row['syn']: self.assertIsNone(row['sor'])
            else:
                result=method['teams'][row['t']]
                self.assertEqual(result['games'],row['g'])
                self.assertEqual(result['wins'],row['w'])
                rank=1+sum(round(t['match_probability'],12)<round(result['match_probability'],12) for t in method['teams'].values())
                self.assertEqual(row['sor'],rank)
        for key in before:
            if key not in ['sorMethod','values','ratings','statMeta','nationalLeaders']:
                self.assertEqual(before[key],d[key])
        for t in d['teams']:
            for key in before['values'][t]:
                if key!='sor':self.assertEqual(before['values'][t][key],d['values'][t][key])
        for a,b in zip(before['ratings'],d['ratings']):
            self.assertEqual({k:v for k,v in a.items() if k!='sor'},{k:v for k,v in b.items() if k!='sor'})
        broken=copy.deepcopy(before);broken['scoreboard'][0]['as']+=1
        with self.assertRaises(ValueError):update_sor(broken,source)

if __name__=='__main__': unittest.main()
