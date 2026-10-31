"""Combine embedding candidates, conservative wording rules, and contextual review.

The analysis overlay never edits source annotations or assigns new taxonomy IDs.
"""
from collections import Counter, defaultdict
import csv
import hashlib
import html
import json
import math
from pathlib import Path
import re

import numpy as np

ROOT = Path('reports/semantic-audit')
SOURCE = Path('data/EgoContact/annotations/24_04_2026.json')


def normalize(text):
    return re.sub(r'\s+', ' ', (text or '').replace('_', ' ').strip().lower())


def metrics(counts):
    values = sorted(counts.values(), reverse=True)
    total = sum(values)
    entropy = -sum((n / total) * math.log2(n / total) for n in values) if total else 0
    return {'events': total, 'distinctValues': len(values),
            'singletonValues': sum(n == 1 for n in values),
            'valuesWithAtMost5Events': sum(n <= 5 for n in values),
            'top1Percent': round(100 * sum(values[:1]) / total, 4) if total else 0,
            'top2Percent': round(100 * sum(values[:2]) / total, 4) if total else 0,
            'top10Percent': round(100 * sum(values[:10]) / total, 4) if total else 0,
            'entropyBits': round(entropy, 5), 'effectiveValues': round(2 ** entropy, 3)}


def main():
    raw = SOURCE.read_bytes()
    events = json.loads(raw)
    rules = json.loads(Path('scripts/semantic_review_rules.json').read_text())
    method = json.loads((ROOT / 'embedding-method.json').read_text())
    assert method['sourceSha256'] == hashlib.sha256(raw).hexdigest()
    baseline = json.loads((ROOT / 'summary.json').read_text())
    assert baseline['sourceSha256'] == method['sourceSha256']
    report = {'sourceSha256': method['sourceSha256'], 'events': len(events), 'embedding': method,
              'taxonomyStatus': 'Awaiting original STA taxonomy; IDs are observed assignments, not verified canonical classes.',
              'normalizationPolicy': 'Case/whitespace/underscore normalization plus explicit inflection, plural, and wording rules. No semantic nearest-neighbor merges. Different object modifiers, mechanisms, directions, and action states remain separate. These counts are phrase inventories, not verified class counts.',
              'dimensions': {}, 'pairDecisions': [], 'eventDecisions': [], 'candidateAssignments': []}
    overlay = []
    for dim, field, idfield, alias_key in [('actions', 'action', 'ego4d_verb_id', 'action_aliases'), ('objects', 'object', 'ego4d_noun_id', 'object_aliases')]:
        aliases = rules[alias_key]
        assert not set(aliases.values()).intersection(aliases), 'Alias chains require explicit resolution'
        normalized, reviewed, stored = Counter(), Counter(), Counter()
        phrase_ids = defaultdict(Counter)
        changed = 0
        neighbors = json.loads((ROOT / f'{dim}-neighbors.json').read_text())
        lookup = {r['phrase']: r for r in neighbors}
        embeddings = np.load(ROOT / f'{dim}-embeddings.npz')
        words = embeddings['phrases'].tolist()
        vectors = embeddings['vectors']
        assert np.allclose(np.linalg.norm(vectors, axis=1), 1, atol=1e-5)
        index = {word: i for i, word in enumerate(words)}
        for key, event in events.items():
            sem = event.get('semantic_annotation', {})
            phrase, category_id = normalize(sem.get(field)), sem.get(idfield)
            if phrase:
                normalized[phrase] += 1
                target = aliases.get(phrase, phrase)
                reviewed[target] += 1
                changed += target != phrase
                phrase_ids[phrase][str(category_id)] += 1
                if target != phrase:
                    overlay.append({'event_id': key, 'dimension': dim, 'original_phrase': sem[field], 'normalized_phrase': phrase,
                                    'reviewed_phrase': target, 'stored_id': category_id,
                                    'reason': 'explicit_surface_normalization', 'taxonomy_id_changed': False})
            if type(category_id) is int and category_id >= 0:
                stored[category_id] += 1
        for decision in rules['pair_decisions']:
            if decision['dimension'] != dim:
                continue
            a, b = decision['a'], decision['b']
            cosine = float(vectors[index[a]] @ vectors[index[b]]) if a in index and b in index else None
            report['pairDecisions'].append({**decision, 'cosine': round(cosine, 6) if cosine is not None else None,
                                           'counts': [normalized[a], normalized[b]]})
        # Consistency candidates: exact same phrase, >=10 observations, >=95% of
        # all occurrences share an existing nonnegative ID. No semantic merging.
        candidates = {}
        for phrase, ids in phrase_ids.items():
            valid = {int(i): n for i, n in ids.items() if i != 'None' and int(i) >= 0}
            if not valid:
                continue
            best = sorted(valid, key=lambda i: (-valid[i], i))[0]
            support, total = valid[best], sum(ids.values())
            if total >= 10 and support / total >= 0.95:
                candidates[phrase] = (best, support, total)
        for key, event in events.items():
            sem = event.get('semantic_annotation', {})
            phrase, category_id = normalize(sem.get(field)), sem.get(idfield)
            if phrase in candidates and category_id != candidates[phrase][0]:
                best, support, total = candidates[phrase]
                report['candidateAssignments'].append({'event_id': key, 'dimension': dim, 'phrase': phrase,
                    'stored_id': category_id, 'candidate_id': best, 'support': support, 'phrase_events': total,
                    'support_fraction': round(support / total, 6), 'status': 'review_only_not_applied',
                    'description': sem.get('interaction_description', '')})
        report['dimensions'][dim] = {'storedIds': metrics(stored), 'normalizedPhrases': metrics(normalized),
            'reviewedPhrases': metrics(reviewed), 'eventsWithSurfaceNormalization': changed,
            'unmappedEvents': baseline['dimensions'][dim]['unmappedEvents'],
            'missingEvents': baseline['dimensions'][dim]['missingEvents'],
            'phraseInventory': [{'phrase': phrase, 'count': count} for phrase, count in reviewed.most_common()],
            'neighbors': neighbors}
        assert sum(reviewed.values()) == sum(normalized.values()) == len(events) - 4
    for decision in rules['event_decisions']:
        sem = events[decision['event_id']]['semantic_annotation']
        report['eventDecisions'].append({**decision, 'original': sem, 'applied': False})
    (ROOT / 'reviewed-analysis.json').write_text(json.dumps(report, indent=2) + '\n')
    (ROOT / 'normalization-overlay.json').write_text(json.dumps(overlay, indent=2) + '\n')
    candidates = report['candidateAssignments']
    with (ROOT / 'assignment-candidates.csv').open('w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=['event_id', 'dimension', 'phrase', 'stored_id', 'candidate_id', 'support', 'phrase_events', 'support_fraction', 'status', 'description'])
        writer.writeheader(); writer.writerows(candidates)
    # Standalone interactive report: no server, account, CDN or network needed.
    data = json.dumps(report).replace('<', '\\u003c')
    template = Path('scripts/semantic_report_template.html').read_text()
    (ROOT / 'report.html').write_text(template.replace('__REPORT_DATA__', data))
    for dim, entry in report['dimensions'].items():
        print(dim, {k: v for k, v in entry.items() if k not in ['phraseInventory', 'neighbors']})
    print('assignment candidates', len(candidates), 'event decisions', len(report['eventDecisions']))


if __name__ == '__main__':
    main()
