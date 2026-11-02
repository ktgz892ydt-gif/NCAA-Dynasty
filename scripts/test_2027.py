"""Regular-season boundary and reconciliation checks for the 2027 capture."""
import collections
import unittest
from season_io import ROOT, read
from prepare_2027 import prepare, derive


class RegularSeason2027Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.folder = ROOT / 'data/seasons/2027'
        cls.inputs = cls.folder / 'inputs'
        cls.games = read(cls.inputs / 'scoreboard.json')
        cls.national = read(cls.inputs / 'national-regular-stats.json')
        cls.data = read(cls.folder / 'season.json')

    def test_every_real_team_has_exactly_twelve_games(self):
        appearances = collections.Counter(g[k] for g in self.games for k in ['a', 'h'])
        real = {t: n for t, n in appearances.items() if not t.startswith('FCS')}
        self.assertEqual(len(self.games), 842)
        self.assertEqual(len(real), 138)
        self.assertEqual(set(real.values()), {12})
        self.assertLessEqual(max(g['wk'] for g in self.games), 14)

    def test_postseason_results_are_not_in_the_ratings_inputs(self):
        for a, h, pf, pa in read(self.inputs / 'excluded-postseason-games.json'):
            self.assertFalse(any(
                (g['a'], g['h'], g['as'], g['hs']) in [(a, h, pf, pa), (h, a, pa, pf)]
                for g in self.games), (a, h))
        rivalry = [g for g in self.games
                   if {g['a'], g['h']} == {'Western Michigan', 'Central Michigan'}]
        self.assertEqual(len(rivalry), 1)
        self.assertEqual(sorted([rivalry[0]['as'], rivalry[0]['hs']]), [7, 52])

    def test_independently_recorded_dynasty_scoring_totals(self):
        for short, record, pf, pa in [
            ('W. Michigan', '11-1', 380, 193),
            ('E. Michigan', '4-8', 202, 227),
            ('C. Michigan', '11-1', 396, 142),
        ]:
            cells = self.data['values'][short]
            self.assertEqual((cells['record']['v'], cells['pts']['v'], cells['ptsa']['v']),
                             (record, pf, pa))
            self.assertEqual(len(self.data['schedules'][short]), 12)

    def test_one_and_two_postseason_games_are_subtracted(self):
        # Verified from the independently captured season screens and game boxes.
        wmu = self.national['Western Michigan']
        cmu = self.national['Central Michigan']
        self.assertEqual(wmu['yds'], 5374 - 331)
        self.assertEqual(cmu['yds'], 4624 - 189 - 359)
        self.assertEqual((wmu['pcomp'], wmu['patt']), (245 - 21, 362 - 31))
        self.assertEqual((cmu['pcomp'], cmu['patt']), (212 - 12 - 19, 288 - 15 - 26))
        self.assertEqual(wmu['puntyds'], 1080 - 98)
        self.assertEqual(cmu['puntyds'], 1312 - 144 - 118)

    def test_rates_are_recomputed_from_regular_season_counts(self):
        for full, short in [('Western Michigan', 'W. Michigan'),
                            ('Central Michigan', 'C. Michigan'),
                            ('Eastern Michigan', 'E. Michigan')]:
            s = self.national[full]
            cells = self.data['values'][short]
            self.assertAlmostEqual(cells['ypp']['v'], s['yds'] / (s['car'] + s['patt']))
            self.assertAlmostEqual(cells['pcpct']['v'], s['pcomp'] / s['patt'])
            self.assertAlmostEqual(cells['d3pct']['v'], s['d3c'] / s['d3a'])

    def test_last_championship_photos_complete_team_deductions(self):
        self.assertEqual(read(self.inputs/'pending-source-fields.json'), [])
        captured=read(self.inputs/'captured-team-stats.json')
        for team,yds,pyds,rtd,third,redzone,penyds in [
            ('Arkansas State',498,388,4,4,6,85),
            ('Coastal Carolina',390,179,3,6,6,61)]:
            c=captured[team];s=self.national[team]
            self.assertEqual(s['games'],12)
            self.assertEqual(s['yds'],c['OFFENSE']['OFF']-yds)
            self.assertEqual(s['pyds'],c['OFFENSE']['PASS']-pyds)
            self.assertEqual(s['rtd'],c['OFFENSE']['RTD']-rtd)
            self.assertEqual(s['d3c'],c['CONVERSIONS']['3DC']-third)
            self.assertEqual(s['rza'],c['REDZONE EFFICIENCY']['ATT']-redzone)
            self.assertEqual(s['penyds'],c['PENALTIES']['YARDS']-penyds)
        self.assertEqual(self.data['nationalStatCoverage']['pyds']['teams'],138)
        self.assertEqual(self.data['coverage']['photos'],2)

    def test_player_games_played_preserve_actual_appearances(self):
        # A season GP of 12 does not prove regular-season-only player coverage.
        captured = read(self.inputs / 'captured-dynasty-players.json')
        kicker = captured['Western Michigan']['KICKING'][0]
        self.assertEqual(kicker['values']['GP'], 12)
        regular = next(r for r in self.data['playerLeaders']['KICKING']['rows'] if r['name'] == kicker['name'])
        self.assertEqual(regular['values']['GP'], 11)
        self.assertEqual((regular['values']['FGM'], regular['values']['FGA']), (10, 15))
        self.assertEqual(self.data['values']['W. Michigan']['fgm']['v'], 10)

    def test_national_ranks_use_only_available_regular_season_values(self):
        metrics = {m['key']: m for m in self.data['statMeta']}
        derived = {t: derive(s) for t, s in self.national.items()}
        for key, coverage in self.data['nationalStatCoverage'].items():
            eligible = {t: v[key] for t, v in derived.items() if v.get(key) is not None}
            self.assertEqual(coverage['teams'], len(eligible), key)
            high = metrics[key].get('higherBetter') is not False
            expected = sorted(eligible.items(), key=lambda kv: ((-kv[1] if high else kv[1]), kv[0]))[:10]
            self.assertEqual(self.data['nationalLeaders'][key],
                             [{'t': t, 'v': v} for t, v in expected], key)

    def test_prepared_inputs_are_reproducible_from_retained_sources(self):
        folder, outputs = prepare()
        for name, data in outputs.items():
            self.assertEqual(data, read(folder / 'inputs' / name), name)

    def test_partial_player_capture_is_explicit(self):
        for category, coverage in self.data['leaderCoverage'].items():
            self.assertFalse(coverage['nationalComplete'], category)
            self.assertIn('12-game', coverage['scope'])
            self.assertIn('ambiguous matches are withheld', coverage['scope'])

    def test_player_offense_matches_team_totals_after_deductions(self):
        players = read(self.inputs / 'regular-dynasty-players.json')
        for team, cats in players.items():
            totals = self.national[team]
            for cat, fields in [('PASSING', {'YARDS':'pyds','TD':'ptd','COMP':'pcomp','ATT':'patt','SACKS':'sackstaken'}),
                                ('RUSHING', {'YARDS':'ryds','TD':'rtd','CAR':'car'}),
                                ('RECEIVING', {'YARDS':'pyds','TD':'ptd'})]:
                for field, metric in fields.items():
                    self.assertTrue(all(r['values'].get(field) is not None for r in cats[cat]), (team,cat,field))
                    self.assertEqual(sum(r['values'][field] for r in cats[cat]), totals[metric], (team,cat,field))
        qb_rush=next(r for r in players['Western Michigan']['RUSHING'] if r['name']=='R.Montgomery')
        self.assertEqual(qb_rush['values']['YARDS'], -18)

    def test_defensive_and_specialist_deductions(self):
        for team, sacks, tfl, fgm, fga in [('Western Michigan',22,54,10,15),('Central Michigan',31,89,15,18),('Eastern Michigan',18,86,13,16)]:
            s=self.national[team]
            self.assertEqual((s['sacks'],s['tfl'],s['fgm'],s['fga']), (sacks,tfl,fgm,fga))
        self.assertEqual(self.data['nationalStatCoverage']['sacks']['teams'],138)

    def test_player_cutoff_and_count_identities(self):
        for cat, source in self.data['playerLeaders'].items():
            for r in source['rows']:
                v=r['values']
                if v.get('GP') is not None:self.assertTrue(0 <= v['GP'] <= 12, (cat,r['name']))
                if cat=='DEFENSE' and all(v.get(k) is not None for k in ['SOLO','ASSISTS','TAK']):
                    self.assertEqual(v['SOLO']+v['ASSISTS'],v['TAK'],r['name'])
                if cat=='KICKING':
                    for pre in ['FGM','FGA']:
                        keys=[pre+s for s in ['29','39','49','50']]
                        if all(v.get(k) is not None for k in keys+[pre]):self.assertEqual(sum(v[k] for k in keys),v[pre],r['name'])

    def test_user_requested_taylor_split_is_explicit_and_conserves_totals(self):
        rows=[r for r in self.data['playerLeaders']['DEFENSE']['rows'] if r['team']=='Central Michigan' and r['name']=='J.Taylor']
        self.assertEqual(len(rows),2)
        self.assertTrue(all(r['estimate'] for r in rows))
        by_pos={r['pos']:r['values'] for r in rows}
        self.assertEqual((by_pos['WILL']['TAK'],by_pos['FS']['TAK']),(62,51))
        self.assertEqual(sum(r['values']['TFL'] for r in rows),18)
        self.assertEqual(sum(r['values']['TAK'] for r in rows),74+63-6-3-8-7)

    def test_av_uses_regular_inputs_and_declared_populations(self):
        notes=self.data['avNotes'];population=read(self.inputs/'av-baseline-players.json')
        self.assertEqual(notes['league']['population']['qualifiedPassers'],len(population['PASSING']))
        q=[r['values'] for r in population['PASSING']]
        self.assertTrue(all(v['ATT']>=150 for v in q))
        self.assertAlmostEqual(notes['league']['aya'],sum(v['YARDS']+20*v['TD']-45*v['INT'] for v in q)/sum(v['ATT'] for v in q))
        for full,short in [('Western Michigan','W. Michigan'),('Central Michigan','C. Michigan'),('Eastern Michigan','E. Michigan')]:
            s=self.national[full];drives=s['ptd']+s['rtd']+s['fga']+s['punts']+s['give']+s['d4a']-s['d4c']+24
            self.assertEqual(notes[full]['drives'],drives)
            self.assertIsNotNone(self.data['values'][short]['av_kicker']['v'])
            self.assertTrue(self.data['values'][short]['av_qb1']['estimate'])


if __name__ == '__main__':
    unittest.main()
