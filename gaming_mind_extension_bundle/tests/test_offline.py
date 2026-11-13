"""Unit tests that do not contact PEP and contain no PEP records."""
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
import pandas as pd

HERE = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('gaming_extension_test', HERE / 'gaming_extension.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class OfflineTests(unittest.TestCase):
    def test_eight_distinct_codes(self):
        codes = [v['pep_prefix'] for v in module.JOURNALS.values()]
        self.assertEqual(len(codes), 8)
        self.assertEqual(len(set(codes)), 8)

    def test_screen_candidates_without_inventing_relevance(self):
        df = pd.DataFrame([
            {'document_id': 'X1', 'year_for_analysis': '2019', 'journal_key': 'fake',
             'title_clean': 'Therapy and Minecraft', 'abstract_clean': 'A clinical example.',
             'text_for_analysis': 'Therapy and Minecraft. A clinical example.'},
            {'document_id': 'X2', 'year_for_analysis': '2020', 'journal_key': 'fake',
             'title_clean': 'Role-playing in psychotherapy', 'abstract_clean': '',
             'text_for_analysis': 'Role-playing in psychotherapy.'},
            {'document_id': 'X3', 'year_for_analysis': '2021', 'journal_key': 'fake',
             'title_clean': 'Object relations', 'abstract_clean': '',
             'text_for_analysis': 'Object relations.'}])
        with tempfile.TemporaryDirectory() as d:
            module.screen(df, Path(d))
            out = pd.read_csv(Path(d) / 'gaming_candidate_review_queue.csv')
            self.assertEqual(len(out), 2)
            self.assertEqual(out.iloc[0]['match_tier'], 'strong')
            self.assertEqual(out.iloc[1]['match_tier'], 'needs_context')
            self.assertTrue(pd.isna(out.iloc[1]['manual_decision']))

    def test_date_range_config(self):
        self.assertEqual(module.CONFIG['analysis_period'], [1970, 2025])
        self.assertEqual(max(1970, module.JOURNALS['psychoanalytic_quarterly']['first_year']), 1970)
        self.assertEqual(max(1970, module.JOURNALS['neuropsychoanalysis']['first_year']), 1999)


if __name__ == '__main__':
    unittest.main()
