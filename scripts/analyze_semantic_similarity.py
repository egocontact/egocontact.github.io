"""Local embedding audit; similarities are candidates, never automatic merges.

Run with Python containing torch, transformers and numpy. All annotation text stays
local. Model weights are downloaded from Hugging Face and their revision recorded.
"""
import argparse
from collections import Counter, defaultdict
import hashlib
import json
from pathlib import Path
import re

import numpy as np
import torch
from transformers import AutoModel, AutoTokenizer


def normalize(text):
    return re.sub(r'\s+', ' ', (text or '').replace('_', ' ').strip().lower())


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--source', type=Path, default=Path('data/EgoContact/annotations/24_04_2026.json'))
    p.add_argument('--output', type=Path, default=Path('reports/semantic-audit'))
    p.add_argument('--model', default='sentence-transformers/all-MiniLM-L6-v2')
    p.add_argument('--revision', default='main')
    args = p.parse_args()
    raw = args.source.read_bytes()
    events = json.loads(raw)
    torch.set_num_threads(4)
    tokenizer = AutoTokenizer.from_pretrained(args.model, revision=args.revision)
    model = AutoModel.from_pretrained(args.model, revision=args.revision).eval()
    device = 'cuda' if torch.cuda.is_available() else 'cpu'
    model.to(device)
    args.output.mkdir(parents=True, exist_ok=True)
    metadata = {'model': args.model, 'revision': getattr(model.config, '_commit_hash', args.revision),
                'pooling': 'attention-masked mean; L2 normalized; cosine similarity',
                'sourceSha256': hashlib.sha256(raw).hexdigest(),
                'automaticMerges': 0, 'dimensions': {}}
    for dimension, field, idfield in [('actions', 'action', 'ego4d_verb_id'), ('objects', 'object', 'ego4d_noun_id')]:
        counts, examples, ids = Counter(), defaultdict(list), defaultdict(Counter)
        for event_id, event in events.items():
            sem = event.get('semantic_annotation', {})
            phrase = normalize(sem.get(field))
            if not phrase:
                continue
            counts[phrase] += 1
            ids[phrase][str(sem.get(idfield))] += 1
            if len(examples[phrase]) < 4:
                examples[phrase].append({'event_id': event_id, 'description': sem.get('interaction_description', '')})
        phrases = sorted(counts, key=lambda phrase: (-counts[phrase], phrase))
        vectors = []
        for start in range(0, len(phrases), 64):
            batch = tokenizer(phrases[start:start + 64], padding=True, truncation=True, max_length=128, return_tensors='pt').to(device)
            with torch.inference_mode():
                out = model(**batch).last_hidden_state
                mask = batch['attention_mask'].unsqueeze(-1)
                vector = (out * mask).sum(1) / mask.sum(1).clamp(min=1)
                vectors.append(torch.nn.functional.normalize(vector, p=2, dim=1).cpu().numpy())
        vectors = np.concatenate(vectors)
        sim = vectors @ vectors.T
        np.fill_diagonal(sim, -np.inf)
        rows = []
        for i, phrase in enumerate(phrases):
            nearest = np.argsort(-sim[i], kind='stable')[:8]
            rows.append({'phrase': phrase, 'count': counts[phrase], 'storedIds': dict(ids[phrase]),
                         'examples': examples[phrase],
                         'neighbors': [{'phrase': phrases[j], 'cosine': round(float(sim[i, j]), 6), 'count': counts[phrases[j]]} for j in nearest]})
        # Persist pairwise action similarity so any verb pair can be inspected.
        np.savez_compressed(args.output / f'{dimension}-embeddings.npz', phrases=np.array(phrases), vectors=vectors)
        (args.output / f'{dimension}-neighbors.json').write_text(json.dumps(rows, indent=2) + '\n')
        metadata['dimensions'][dimension] = {'normalizedPhrases': len(phrases), 'events': sum(counts.values()), 'missing': len(events) - sum(counts.values())}
        print(dimension, metadata['dimensions'][dimension], flush=True)
    (args.output / 'embedding-method.json').write_text(json.dumps(metadata, indent=2) + '\n')


if __name__ == '__main__':
    main()
