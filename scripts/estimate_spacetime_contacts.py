"""Estimate demo-only contact paths between annotated endpoints.

Run after prepare_spacetime.py: /usr/bin/python3 scripts/estimate_spacetime_contacts.py
Requires OpenCV and NumPy. Reads exported frames; never modifies dataset labels.
"""

import argparse
import json
from pathlib import Path

import cv2
import numpy as np


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--manifest', type=Path, default=Path('static/data/spacetime/manifest.json'))
    parser.add_argument('--static', type=Path, default=Path('static'))
    parser.add_argument('--preview', type=Path, default=Path('tmp/visual-qa/contact-tracks.jpg'))
    args = parser.parse_args()
    data = json.loads(args.manifest.read_text())
    frames = data['frames']
    assert frames[0]['index'] == data['observation'] and frames[-1]['index'] == data['contact']
    images = [cv2.imread(str(args.static / frame['src'].lstrip('/'))) for frame in frames]
    if any(image is None for image in images):
        raise RuntimeError('Exported frames are missing; run prepare_spacetime.py first.')
    gray = [cv2.cvtColor(image, cv2.COLOR_BGR2GRAY) for image in images]
    height, width = gray[0].shape
    scale = np.array([width / data['width'], height / data['height']], np.float32)
    keys = ['contact_thumb', 'contact_index']

    def anchor(frame):
        return np.array([[data['anchors'][str(frame)][key]['x'], data['anchors'][str(frame)][key]['y']]
                         for key in keys], np.float32) * scale

    params = dict(winSize=(31, 31), maxLevel=3,
                  criteria=(cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT, 40, .001),
                  minEigThreshold=1e-5)
    current = anchor(data['observation']).reshape(-1, 1, 2)
    positions = [current[:, 0, :].copy()]
    fb_errors = [np.zeros(len(keys))]
    for before, after in zip(gray, gray[1:]):
        tracked, status, _ = cv2.calcOpticalFlowPyrLK(before, after, current, None, **params)
        if tracked is None or not np.all(status):
            raise RuntimeError('Optical flow lost a point; review this event manually.')
        backward, back_status, _ = cv2.calcOpticalFlowPyrLK(after, before, tracked, None, **params)
        if backward is None or not np.all(back_status):
            raise RuntimeError('The reverse-step consistency check failed.')
        error = np.linalg.norm(backward[:, 0, :] - current[:, 0, :], axis=1)
        if not np.isfinite(tracked).all() or np.any(error > 2):
            raise RuntimeError(f'Unreliable flow: round-trip error {error.tolist()} pixels.')
        positions.append(tracked[:, 0, :].copy())
        fb_errors.append(error)
        current = tracked
    positions = np.array(positions)
    fb_errors = np.array(fb_errors)
    endpoint_delta = anchor(data['contact']) - positions[-1]
    drift = np.linalg.norm(endpoint_delta, axis=1)
    if np.any(drift > .04 * np.hypot(width, height)):
        raise RuntimeError(f'Endpoint drift too large to bridge: {drift.tolist()} pixels.')
    times = np.array([(frame['index'] - data['observation']) / (data['contact'] - data['observation']) for frame in frames])
    # This is an explicit visualization constraint, not an optical-flow measurement.
    weights = times * times * (3 - 2 * times)
    corrected = positions + weights[:, None, None] * endpoint_delta
    if (np.any(corrected[:, :, 0] < 0) or np.any(corrected[:, :, 0] >= width)
            or np.any(corrected[:, :, 1] < 0) or np.any(corrected[:, :, 1] >= height)):
        raise RuntimeError('Estimated points left the image.')
    tracks = {}
    for k, key in enumerate(keys):
        tracks[key] = [
            {'frame': frame['index'], 'x': float(point[0] / scale[0]), 'y': float(point[1] / scale[1]),
             'annotated': i in (0, len(frames)-1)}
            for i, (frame, point) in enumerate(zip(frames, corrected[:, k]))
        ]
        # Preserve original endpoint coordinates exactly, without float32 rounding.
        for i, frame in ((0, data['observation']), (-1, data['contact'])):
            tracks[key][i].update({axis: data['anchors'][str(frame)][key][axis] for axis in ('x', 'y')})
    data['estimated_tracks'] = {
        'method': 'Forward pyramidal Lucas–Kanade with smooth endpoint correction',
        'purpose': 'Visualization only; intermediate positions are not dataset annotations',
        'opencv_version': cv2.__version__, 'tracking_resolution': [width, height],
        'max_roundtrip_error_px': dict(zip(keys, fb_errors.max(axis=0).tolist())),
        'uncorrected_endpoint_error_px': dict(zip(keys, drift.tolist())),
        'paths': tracks,
    }
    previews = []
    for i, image in enumerate(images):
        preview = image.copy()
        for k, color in enumerate(((255, 186, 57), (196, 106, 243))):
            point = tuple(np.round(corrected[i, k]).astype(int))
            cv2.circle(preview, point, 4, color, 2, cv2.LINE_AA)
        label = 'annotated' if i in (0, len(frames)-1) else 'estimated'
        cv2.putText(preview, f"{frames[i]['index']}  {label}", (12, 25), cv2.FONT_HERSHEY_SIMPLEX, .6, (255, 255, 255), 2)
        previews.append(cv2.resize(preview, (320, 240)))
    while len(previews) % 4:
        previews.append(np.zeros_like(previews[0]))
    montage = np.concatenate([np.concatenate(previews[i:i+4], axis=1) for i in range(0, len(previews), 4)], axis=0)
    args.preview.parent.mkdir(parents=True, exist_ok=True)
    if not cv2.imwrite(str(args.preview), montage):
        raise RuntimeError('Could not save the review montage.')
    args.manifest.write_text(json.dumps(data, indent=2) + '\n')
    print(f'Estimated {len(frames)} positions per contact. Review: {args.preview}')
    print('Maximum round-trip errors (tracking pixels):', fb_errors.max(axis=0))
    print('Uncorrected endpoint errors (tracking pixels):', drift)


if __name__ == '__main__':
    main()
