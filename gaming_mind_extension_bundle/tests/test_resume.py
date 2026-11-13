"""Offline regression tests for safe year-by-year resume (no PEP requests)."""
import csv
import importlib.util
from pathlib import Path
import tempfile
import unittest

import pandas as pd

HERE = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('gaming_resume_test', HERE / 'gaming_extension.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class ResumeCheckpointTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.out = Path(self.temp.name)
        self.journal = 'modern_psychoanalysis'
        self.prefix = 'MPSA'

    def artifacts(self, year):
        p = module.file_paths(self.out, 'harvest', self.journal, year)
        p['raw'].mkdir(parents=True, exist_ok=True)
        (p['raw'] / 'response.json').write_text('{}', encoding='utf-8')
        for key in ('articles', 'keywords', 'log'):
            p[key].parent.mkdir(parents=True, exist_ok=True)
        return p

    def store(self, year, ids, status):
        p = self.artifacts(year)
        pd.DataFrame({'document_id': ids}).to_csv(p['articles'], index=False)
        pd.DataFrame(columns=['keyword_raw']).to_csv(p['keywords'], index=False)
        pd.DataFrame([{'status_code': '200', 'error': ''}]).to_csv(p['log'], index=False)
        manifest = pd.DataFrame([{'journal': self.journal, 'year': str(year),
                                  'status': status, 'n_rows': str(len(ids))}])
        return p, manifest

    def test_valid_complete_year_is_skipped(self):
        paths, manifest = self.store(2017, ['MPSA.041.0001'], 'ok')
        self.assertEqual(module.checkpoint_state(manifest, paths, self.journal, 2017,
                                                  self.prefix, 'harvest'), 'complete')

    def test_empty_http200_is_not_complete(self):
        paths, manifest = self.store(2018, [], 'empty')
        self.assertEqual(module.checkpoint_state(manifest, paths, self.journal, 2018,
                                                  self.prefix, 'harvest'), 'unverified_empty')

    def test_missing_log_stops_before_network(self):
        paths, manifest = self.store(2017, ['MPSA.041.0001'], 'ok')
        paths['log'].unlink()
        with self.assertRaises(SystemExit):
            module.checkpoint_state(manifest, paths, self.journal, 2017,
                                    self.prefix, 'harvest')

    def test_mismatched_manifest_count_stops(self):
        paths, manifest = self.store(2017, ['MPSA.041.0001'], 'ok')
        manifest.loc[0, 'n_rows'] = '12'
        with self.assertRaises(SystemExit):
            module.checkpoint_state(manifest, paths, self.journal, 2017,
                                    self.prefix, 'harvest')

    def test_wrong_prefix_stops(self):
        paths, manifest = self.store(2017, ['OTHER.001.0001'], 'ok')
        with self.assertRaises(SystemExit):
            module.checkpoint_state(manifest, paths, self.journal, 2017,
                                    self.prefix, 'harvest')

    def test_new_year_has_no_files(self):
        paths = module.file_paths(self.out, 'harvest', self.journal, 2019)
        self.assertEqual(module.checkpoint_state(pd.DataFrame(), paths, self.journal, 2019,
                                                  self.prefix, 'harvest'), 'new')

    def test_gap_selection_is_explicit(self):
        self.assertEqual(
            module.gap_selection(['modern_psychoanalysis:2018'], [self.journal]),
            {(self.journal, 2018)})
        with self.assertRaises(SystemExit):
            module.gap_selection(['modern_psychoanalysis:1960'], [self.journal])
        with self.assertRaises(SystemExit):
            module.gap_selection(['psychoanalytic_quarterly:2018'], [self.journal])


if __name__ == '__main__':
    unittest.main()
