"""Export real, sparsely sampled video frames and the two annotated anchors.

Run from the repository root: python scripts/prepare_spacetime.py
Requires ffmpeg on PATH; no Python packages are needed.
"""

import argparse
import json
from pathlib import Path
import subprocess


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--event', default='8f339122-0193-4191-a0ea-d761b08ffffe_10009')
    parser.add_argument('--annotations', type=Path, default=Path('data/EgoContact/annotations/24_04_2026.json'))
    parser.add_argument('--videos', type=Path, default=Path('data/Ego4D'))
    parser.add_argument('--output', type=Path, default=Path('static/data/spacetime'))
    args = parser.parse_args()
    annotation = json.loads(args.annotations.read_text())[args.event]
    observation = annotation['last_prediction_frame']
    first = observation
    contact = annotation['contact_frame']
    assert observation < contact, 'Invalid temporal anchors'
    sample_count = min(24, contact - first + 1)
    indices = sorted({round(first + (contact-first)*i/(sample_count-1)) for i in range(sample_count)})
    output = args.output / args.event
    output.mkdir(parents=True, exist_ok=True)
    # Decode by zero-based frame number, never approximate seeks or synthesize frames.
    selection = '+'.join(f'eq(n,{index})' for index in indices)
    subprocess.run([
        'ffmpeg', '-hide_banner', '-loglevel', 'error', '-y',
        '-i', str(args.videos / (annotation['clip_id'] + '.mp4')),
        '-vf', f"select='{selection}',scale=480:-2", '-fps_mode', 'vfr',
        '-frames:v', str(len(indices)), '-start_number', '0', '-q:v', '3',
        str(output / '%03d.jpg'),
    ], check=True)
    frames = []
    for i, index in enumerate(indices):
        path = output / f'{i:03d}.jpg'
        if not path.exists():
            raise RuntimeError(f'Missing extracted frame {index}')
        frames.append({'index': index, 'src': f'/data/spacetime/{args.event}/{path.name}'})
    manifest = {
        'event': args.event, 'action': annotation['semantic_annotation']['interaction_description'],
        'width': annotation['frame_width'], 'height': annotation['frame_height'],
        'fps': annotation['fps'], 'first': first, 'observation': observation, 'contact': contact,
        'anchors': {str(index): annotation['per_frame_annotations'][str(index)] for index in (observation, contact)},
        'frames': frames,
    }
    (args.output / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
    # Remove surplus exports left by a previously longer interval, after success.
    expected = {f'{i:03d}.jpg' for i in range(len(indices))}
    for path in output.glob('[0-9][0-9][0-9].jpg'):
        if path.name not in expected:
            path.unlink()
    print(f'Exported {len(frames)} real frames to {output}')


if __name__ == '__main__':
    main()
