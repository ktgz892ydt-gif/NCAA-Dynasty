"""Cross-season isolation and independent migration baseline checks."""
import copy
import json
import shutil
import tempfile
import unittest
from pathlib import Path
from build_season import build
from init_season import initialize
from publish_season import publish
from preview import preview_manifest
from season_io import ROOT, read, atomic_write, season_dir, validate_games, validate_output


class MultiSeasonTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup);self.root=Path(self.temp.name)
        shutil.copytree(ROOT/'config',self.root/'config')
        (self.root/'data').mkdir();shutil.copyfile(ROOT/'data/seasons.json',self.root/'data/seasons.json')

    def draft(self,year='2027'):
        folder=initialize(year,self.root)
        # A connected three-team schedule with both wins and losses. SOR requires 25 FBS teams and remains unavailable.
        games=[{'wk':0,'a':'Western Michigan','h':'Eastern Michigan','as':21,'hs':14,'n':False},
               {'wk':1,'a':'Eastern Michigan','h':'Central Michigan','as':17,'hs':14,'n':False},
               {'wk':2,'a':'Central Michigan','h':'Western Michigan','as':10,'hs':24,'n':True}]
        atomic_write(folder/'inputs/scoreboard.json',games)
        return folder

    def test_2026_matches_independent_baseline(self):
        baseline=read(ROOT/'tests/fixtures/2026-baseline.json');generated=build('2026')
        self.assertEqual({k:generated[k] for k in baseline},baseline)

    def test_new_season_starts_empty_and_unpublished(self):
        before=(self.root/'data/seasons.json').read_bytes();folder=initialize('2027',self.root)
        self.assertEqual(read(folder/'inputs/team-stats.json'),{})
        self.assertEqual(read(folder/'summaries.json'),[])
        data=build('2027',self.root)
        self.assertIsNone(data['values']['W. Michigan']['record']['v'])
        self.assertEqual(data['ratings'],[])
        self.assertEqual((self.root/'data/seasons.json').read_bytes(),before)
        with self.assertRaises(ValueError):initialize('2027',self.root)
        with self.assertRaises(ValueError):season_dir('../2026',self.root)

    def test_build_does_not_read_output_and_preserves_other_seasons(self):
        folder=self.draft();other=initialize('2028',self.root)
        (other/'season.json').write_text('sentinel')
        data=build('2027',self.root);validate_output(data)
        self.assertEqual(data['values']['W. Michigan']['record']['v'],'2-0')
        self.assertIsNone(data['values']['W. Michigan']['sor']['v'])
        self.assertIsNone(data['values']['W. Michigan']['av_team_off']['v'])
        (folder/'season.json').write_text('corrupted generated output')
        self.assertEqual(build('2027',self.root),data)
        self.assertEqual((other/'season.json').read_text(),'sentinel')
        games=read(folder/'inputs/scoreboard.json');games[0]['as']=35;atomic_write(folder/'inputs/scoreboard.json',games)
        changed=build('2027',self.root)
        self.assertNotEqual(data['values']['W. Michigan']['srs'],changed['values']['W. Michigan']['srs'])

    def test_conflicting_games_and_wrong_year_corrections_rejected(self):
        folder=self.draft();games=read(folder/'inputs/scoreboard.json')
        with self.assertRaises(ValueError):validate_games(games+[dict(games[0],hs=6)])
        with self.assertRaises(ValueError):validate_games([dict(games[0],as_=5,n='N')])
        atomic_write(folder/'inputs/corrections.json',{'season':'2026','patches':[]})
        with self.assertRaises(ValueError):build('2027',self.root)

    def test_finalize_then_publish_only_explicitly(self):
        folder=self.draft();atomic_write(folder/'season.json',build('2027',self.root))
        with self.assertRaises(ValueError):publish('2027',self.root)
        meta=read(folder/'metadata.json');meta.update(status='finalized',lastVerified='2027-01-01',regulationGameSeconds=2160)
        atomic_write(folder/'metadata.json',meta)
        atomic_write(folder/'summaries.json',[{'teamId':i,'title':i,'text':'Synthetic test summary.'} for i in meta['teamIds']])
        atomic_write(folder/'season.json',build('2027',self.root));publish('2027',self.root)
        m=read(self.root/'data/seasons.json');self.assertEqual(m['defaultSeason'],'2027');self.assertEqual(len(m['seasons']),2)

    def test_draft_preview_does_not_publish(self):
        folder=self.draft();atomic_write(folder/'season.json',build('2027',self.root))
        before=(self.root/'data/seasons.json').read_bytes()
        preview=preview_manifest('2027',self.root)
        self.assertEqual(preview['defaultSeason'],'2027')
        self.assertIn('(preview)',preview['seasons'][-1]['label'])
        self.assertEqual((self.root/'data/seasons.json').read_bytes(),before)

    def test_no_historical_correction_mode_for_new_year(self):
        folder=self.draft();meta=read(folder/'metadata.json');meta['inputMode']='legacy-2026';atomic_write(folder/'metadata.json',meta)
        with self.assertRaises(ValueError):build('2027',self.root)


if __name__=='__main__':unittest.main()
