"""Regression checks for the counting errors this audit is intended to prevent."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


class FrequencyAuditTests(unittest.TestCase):
    def test_ids_not_strings_and_zero_is_valid(self):
        with tempfile.TemporaryDirectory() as folder:
            folder = Path(folder)
            source = folder / 'source.json'
            events = {}
            for i, (category_id, label) in enumerate([(0, 'adjust'), (0, 'adjust_(regulate)'),
                                                       (1, 'same'), (2, 'same'), (-1, 'new action'),
                                                       (None, None)]):
                events[str(i)] = {'semantic_annotation': {
                    'ego4d_verb_id': category_id, 'ego4d_verb': label,
                    'ego4d_noun_id': category_id, 'ego4d_noun': label}}
            source.write_text(json.dumps(events))
            before = source.read_bytes()
            output = folder / 'distribution.json'
            subprocess.run([sys.executable, str(ROOT / 'scripts/prepare_dataset_distributions.py'),
                            '--source', str(source), '--output', str(output), '--audit-dir', str(folder / 'audit')], check=True, capture_output=True)
            result = json.loads(output.read_text())
            for panel in result['panels']:
                rows = [row for group in panel['groups'] for row in group['rows']]
                self.assertEqual({row['id']: row['count'] for row in rows}, {0: 2, 1: 1, 2: 1})
                self.assertEqual(panel['unmappedEvents'], 1)
                self.assertEqual(panel['missingEvents'], 1)
                self.assertEqual(panel['labelCount'], 3)
            self.assertEqual(before, source.read_bytes())

    def test_real_artifacts_reconcile_and_rules_do_not_merge_opposites(self):
        result = json.loads((ROOT / 'src/lib/data/dataset-distributions.json').read_text())
        analysis = json.loads((ROOT / 'reports/semantic-audit/reviewed-analysis.json').read_text())
        raw = (ROOT / 'data/EgoContact/annotations/24_04_2026.json').read_bytes()
        self.assertEqual(result['sourceSha256'], hashlib.sha256(raw).hexdigest())
        self.assertEqual(result['sourceSha256'], analysis['sourceSha256'])
        for panel in result['panels']:
            rows = [row for group in panel['groups'] for row in group['rows']]
            self.assertEqual(len(rows), len({r['id'] for r in rows}))
            self.assertEqual(sum(r['count'] for r in rows) + panel['unmappedEvents'] + panel['missingEvents'], result['total'])
            metrics = analysis['dimensions'][panel['key']]
            self.assertEqual(metrics['normalizedPhrases']['events'], metrics['reviewedPhrases']['events'])
        rules = json.loads((ROOT / 'scripts/semantic_review_rules.json').read_text())
        for rule in rules['pair_decisions']:
            if rule['decision'] == 'keep_separate':
                aliases = rules['action_aliases' if rule['dimension'] == 'actions' else 'object_aliases']
                self.assertNotEqual(aliases.get(rule['a'], rule['a']), aliases.get(rule['b'], rule['b']))
        self.assertTrue(all(not event['applied'] for event in analysis['eventDecisions']))


if __name__ == '__main__':
    unittest.main()
