"""Select 80 real clip thumbnails from the paper's diversity atlas.

Run from the repository root. Requires ../ral-letter assets and ffmpeg.
The atlas supplies one pre-contact frame per clip; selection favors different
semantic actions. This is an illustrative collage, not a frequency plot.
"""
import json
import random
import subprocess
from collections import defaultdict
from pathlib import Path

source = Path('../ral-letter/assets/teaser/diversity')
manifest = json.loads((source / 'manifest.json').read_text())
events = json.loads(Path('data/EgoContact/annotations/24_04_2026.json').read_text())
groups = defaultdict(list)
for clip in manifest['clips']:
    if 'atlas_index' not in clip:
        continue
    action = events[clip['event_id']].get('semantic_annotation', {}).get('ego4d_verb', '')
    if action:
        groups[action].append(clip)
rng = random.Random(42)
keys = sorted(groups)
rng.shuffle(keys)
selected = [rng.choice(groups[key]) for key in keys[:80]]
chosen = {c['event_id'] for c in selected}
remaining = [c for values in groups.values() for c in values if c['event_id'] not in chosen]
rng.shuffle(remaining)
selected.extend(remaining[:80-len(selected)])
assert len(selected) == 80 and len({c['event_id'] for c in selected}) == 80
Path('src/lib/data/diversity-mosaic.json').write_text(json.dumps([
    {'event': c['event_id'], 'frame': c['frame_index'], 'column': c['atlas_index'] % 64,
     'row': c['atlas_index'] // 64} for c in selected
], indent=2) + '\n')
subprocess.run(['ffmpeg', '-hide_banner', '-loglevel', 'error', '-y', '-i',
                str(source / 'atlas.jpg'), '-frames:v', '1', '-quality', '80',
                'static/images/diversity-atlas.webp'], check=True)
