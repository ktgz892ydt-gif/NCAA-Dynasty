"""Checks on the cross-season written comparison.

The prose is authored, but every number it quotes is stored as a fact and
verified here against both published season files. A figure that drifts out of
agreement with the data fails the build rather than sitting wrong on the page.
"""
import json
import re
import unittest
from season_io import ROOT, read


class ComparisonTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.doc = read(ROOT / 'data/comparisons.json')
        cls.manifest = read(ROOT / 'data/seasons.json')
        cls.seasons = {}
        for entry in cls.manifest['seasons']:
            if entry['published']:
                cls.seasons[entry['id']] = read(ROOT / entry['dataPath'])

    def test_schema_and_generating_block(self):
        self.assertEqual(self.doc['schemaVersion'], 1)
        self.assertIsInstance(self.doc['comparisons'], list)
        self.assertTrue(self.doc['comparisons'])
        gen = self.doc['generating']
        self.assertTrue(gen['label'].strip())
        # the view clamps this, but keep the stored value itself reasonable
        self.assertGreaterEqual(gen['ms'], 800)
        self.assertLessEqual(gen['ms'], 20000)
        self.assertTrue(all(isinstance(s, str) and s.strip() for s in gen['steps']))

    def test_every_comparison_names_published_seasons(self):
        for entry in self.doc['comparisons']:
            self.assertEqual(len(entry['seasons']), len(set(entry['seasons'])))
            for season in entry['seasons']:
                self.assertIn(season, self.seasons, f"{entry['id']} names an unpublished season")
            self.assertTrue(entry['label'].strip())
            self.assertTrue(entry['sections'])
            for section in entry['sections']:
                self.assertTrue(section['heading'].strip())
                self.assertTrue(all(p.strip() for p in section['body']))

    def observed(self, season, fact):
        data = self.seasons[season]
        if fact.get('kind') == 'eff':
            return data['effMethod'][fact['metric']]
        cell = data['values'][fact['team']].get(fact['metric'])
        self.assertIsNotNone(cell, f"{fact['team']} has no {fact['metric']} in {season}")
        return cell['rank'] if fact.get('kind') == 'rank' else cell['v']

    def test_every_quoted_figure_matches_the_season_files(self):
        checked = 0
        for entry in self.doc['comparisons']:
            early, late = entry['seasons'][0], entry['seasons'][-1]
            for section in entry['sections']:
                for fact in section.get('facts', []):
                    self.assertTrue(fact['label'].strip())
                    for season, key in ((early, 'v26'), (late, 'v27')):
                        stored, actual = fact[key], self.observed(season, fact)
                        self.assertIsNotNone(actual, f"{fact['label']} is unavailable in {season}")
                        if isinstance(stored, int) and isinstance(actual, int):
                            self.assertEqual(stored, actual, f"{fact['label']} {season}")
                        else:
                            self.assertAlmostEqual(
                                float(stored), float(actual), delta=0.005,
                                msg=f"{fact['label']} {season}: file says {actual}, comparison says {stored}")
                        checked += 1
        self.assertGreater(checked, 50, 'the comparison should quote a substantial number of figures')

    def test_claims_about_one_sided_metrics_hold(self):
        """The closing section says four measures exist in only one season."""
        early, late = self.seasons['2026'], self.seasons['2027']
        keys = [m['key'] for m in early['statMeta']]
        only_one = []
        for key in keys:
            present = []
            for data in (early, late):
                present.append(any((data['values'][t].get(key) or {}).get('v') is not None
                                   for t in data['teams']))
            if present[0] != present[1]:
                only_one.append(key)
        self.assertEqual(sorted(only_one), ['cfp', 'deftd', 'sttd', 'tfl'])

    def test_the_view_is_wired_up(self):
        shell = (ROOT / 'index.html').read_text()
        self.assertIn('data-v="compare"', shell)
        self.assertIn('id="v-compare"', shell)
        self.assertIn('id="cmp-host"', shell)
        # the tab sits after Leaders, as asked
        self.assertLess(shell.index('data-v="leaders"'), shell.index('data-v="compare"'))
        view = (ROOT / 'assets/views/season.js').read_text()
        self.assertIn("'compare'", view)
        self.assertIn('renderCompare', view)
        loader = (ROOT / 'assets/app.js').read_text()
        self.assertIn("'compare'", loader)
        # the progress panel must never claim a live model call
        for text in re.findall(r"'([^']*)'", view) + re.findall(r'"([^"]*)"', view):
            self.assertNotIn('asking claude', text.lower())


if __name__ == '__main__':
    unittest.main()
