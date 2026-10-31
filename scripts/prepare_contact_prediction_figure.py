#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-only
"""Render Input → Ranked predictions → Evaluation as a static WebP.

Adapted from cppredict/isaac_sim_grasping scripts/figure2.py (c197c04).
License: GPLv3; see LICENSE.figure2. Uses the RQ2 figure's black headings,
dashed enclosures, prompt pill and orange contacts, with softly shadowed photos.
Requires matplotlib, numpy and Pillow.

Run: /usr/bin/python3 scripts/prepare_contact_prediction_figure.py
The observation and stored GT are real; an optional display_contact overrides
the rendered reference for illustration. Ranked predictions are illustrative. Evaluation
zooms into the contact, but computes PCK radii from the FULL image diagonal.
"""
from __future__ import annotations

import argparse
import io
import json
import os
from pathlib import Path
import textwrap

os.environ.setdefault("MPLCONFIGDIR", "/tmp/contact-prediction-matplotlib")
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Circle, FancyArrowPatch, FancyBboxPatch
import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
INK = "#111111"
ORANGE = "#E88B26"
STRICT = "#248AB8"
LOOSE = "#137E83"
# Match the shipped RQ2 asset, including its exact export dimensions.
OUTPUT_WIDTH, OUTPUT_HEIGHT = 2400, 650
CANVAS_WIDTH = 169
CANVAS_HEIGHT = CANVAS_WIDTH * OUTPUT_HEIGHT / OUTPUT_WIDTH
PANEL_WIDTH = 34
PANEL_GAP = 6
# Center the complete illustration, including the mascot.
PIPELINE_WIDTH = 3 * PANEL_WIDTH + 2 * PANEL_GAP
MASCOT_WIDTH, MASCOT_GAP = 23.5, 3
COMPOSITION_LEFT = (CANVAS_WIDTH - PIPELINE_WIDTH - MASCOT_WIDTH - MASCOT_GAP) / 2
PIPELINE_LEFT = COMPOSITION_LEFT + MASCOT_WIDTH + MASCOT_GAP
PANEL_X = tuple(PIPELINE_LEFT + i * (PANEL_WIDTH + PANEL_GAP) for i in range(3))
BODY_Y, BODY_HEIGHT = 2, CANVAS_HEIGHT - 12


def draw_panel(ax, x, title):
    """Black title strip and dashed enclosure adapted from RQ2's figure2.py."""
    ax.add_patch(plt.Rectangle((x, CANVAS_HEIGHT - 7), PANEL_WIDTH, 5.5,
                              facecolor=INK, edgecolor="none"))
    ax.text(x + PANEL_WIDTH / 2, CANVAS_HEIGHT - 4.25, title, ha="center", va="center",
            fontsize=6.6, color="white")
    ax.add_patch(FancyBboxPatch((x, BODY_Y), PANEL_WIDTH, BODY_HEIGHT,
        boxstyle="round,pad=0,rounding_size=2.5", facecolor="none",
        edgecolor="#888888", linewidth=.7, linestyle=(0, (3, 3))))


def image_axes(fig, x, observation, view, *, inset=False):
    """Place rounded photos within each stage, preserving source pixel coordinates."""
    height, width = observation.shape[:2]
    photo_padding = 1.5
    photo_width = PANEL_WIDTH - 4 if inset else PANEL_WIDTH - 2 * photo_padding
    photo_height = 21 * BODY_HEIGHT / PANEL_WIDTH if inset else BODY_HEIGHT - 2 * photo_padding
    photo_x = x + (PANEL_WIDTH - photo_width) / 2
    photo_y = 3.5 if inset else BODY_Y + photo_padding
    # Layer faint, expanding silhouettes for a soft shadow beneath each photo.
    # A separate axes keeps shadows outside the photo's clipping boundary.
    shadow_ax = fig.add_axes([0, 0, 1, 1], xlim=(0, CANVAS_WIDTH),
                             ylim=(0, CANVAS_HEIGHT), zorder=0)
    shadow_ax.set_axis_off()
    radius = 2.5 * photo_width / PANEL_WIDTH
    for spread in np.linspace(.65, .02, 24):
        shadow_ax.add_patch(FancyBboxPatch(
            (photo_x - spread, photo_y - .28 - spread),
            photo_width + 2 * spread, photo_height + 2 * spread,
            boxstyle=f"round,pad=0,rounding_size={radius + spread}",
            facecolor="#263244", edgecolor="none", alpha=.009))
    pane = fig.add_axes([photo_x / CANVAS_WIDTH, photo_y / CANVAS_HEIGHT,
                         photo_width / CANVAS_WIDTH, photo_height / CANVAS_HEIGHT],
                        zorder=1)
    image = pane.imshow(observation, extent=(0, width, height, 0))
    crop_width = view["width"]
    crop_height = crop_width * BODY_HEIGHT / PANEL_WIDTH
    # Widen the input viewport without scaling or stretching its contents.
    if inset:
        crop_width = crop_height * photo_width / photo_height
    else:
        crop_height = crop_width * photo_height / photo_width
    cx, cy = view["center"]
    assert crop_width / 2 <= cx <= width - crop_width / 2
    assert crop_height / 2 <= cy <= height - crop_height / 2
    pane.set_xlim(cx - crop_width / 2, cx + crop_width / 2)
    pane.set_ylim(cy + crop_height / 2, cy - crop_height / 2)
    # Keep rounded photo corners consistent across stages.
    clip = FancyBboxPatch((0, 0), 1, 1, transform=pane.transAxes,
        boxstyle=f"round,pad=0,rounding_size={2.5 / PANEL_WIDTH}",
        mutation_aspect=photo_width / photo_height)
    image.set_clip_path(clip)
    # Mild viewport vignette: darken photo edges without warping the scene.
    # Keep the source frame and annotation coordinates unchanged; markers sit above it.
    yy, xx = np.mgrid[-1:1:256j, -1:1:256j]
    radius = np.sqrt(xx * xx + yy * yy)
    fade = np.clip((radius - .35) / 1.05, 0, 1)
    vignette = np.zeros((256, 256, 4))
    vignette[..., 3] = .36 * fade ** 1.5
    edge_shading = pane.imshow(vignette,
        extent=(cx - crop_width / 2, cx + crop_width / 2,
                cy + crop_height / 2, cy - crop_height / 2),
        interpolation="bilinear", zorder=2)
    edge_shading.set_clip_path(clip)
    pane.add_patch(FancyBboxPatch((0, 0), 1, 1, transform=pane.transAxes,
        boxstyle=f"round,pad=0,rounding_size={2.5 / PANEL_WIDTH}",
        mutation_aspect=photo_width / photo_height, facecolor="none",
        edgecolor="white", linewidth=.6, alpha=.55, zorder=10))
    pane.set_axis_off()
    return pane, clip


def draw_predictions(ax, points, *, detail=False):
    # Identical points, rank numbers and styling in prediction/evaluation panels.
    label_offsets = [(-15, -4), (8, -13), (3, 15), (-14, -16), (14, 4)]
    if detail:
        label_offsets[0] = (8, 12)  # Keep the handle reference marker unobstructed.
        label_offsets[3] = (10, -12)  # Separate the detail labels around the contact.
        label_offsets[4] = (-12, 10)  # Keep the rightmost label inside the detail crop.
    for rank, (point, offset) in enumerate(zip(points, label_offsets), start=1):
        x, y = point["x"], point["y"]
        ax.scatter([x], [y], s=10, c=ORANGE, edgecolors="white",
                   linewidths=.5, zorder=7)
        ax.annotate(str(rank), (x, y), xytext=offset, textcoords="offset points",
                    ha="center", va="center", fontsize=6.3, color=INK,
                    bbox=dict(boxstyle="circle,pad=.15", fc="white", ec=ORANGE, lw=.7),
                    arrowprops=dict(arrowstyle="-", color=ORANGE, lw=.65), zorder=8)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--image", type=Path,
                        default=ROOT / "scripts/assets/contact-prediction-observation.webp")
    parser.add_argument("--example", type=Path,
                        default=ROOT / "scripts/assets/contact-prediction-example.json")
    parser.add_argument("--mascot", type=Path,
                        default=ROOT / "scripts/assets/robot-scratching-head.png")
    parser.add_argument("--output", type=Path,
                        default=ROOT / "static/images/contact-prediction-task.webp")
    args = parser.parse_args()
    data = json.loads(args.example.read_text())
    observation = np.asarray(Image.open(args.image).convert("RGB"))
    width, height = data["width"], data["height"]
    assert observation.shape[:2] == (height, width), "Source must be the full annotated frame."
    points = data["predictions"]
    assert len(points) == 5 and data["predictions_are_illustrative"]
    assert all(0 <= p["x"] < width and 0 <= p["y"] < height for p in points)
    gt = data.get("display_contact", data["ground_truth"])
    diagonal = np.hypot(width, height)
    plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 7})
    fig = plt.figure(figsize=(169 / 25.4, CANVAS_HEIGHT / 25.4), facecolor="white")
    ax = fig.add_axes([0, 0, 1, 1], xlim=(0, CANVAS_WIDTH), ylim=(0, CANVAS_HEIGHT), zorder=3)
    ax.set_axis_off()
    for x, title in zip(PANEL_X, ("Input", "Ranked predictions", "Evaluation")):
        draw_panel(ax, x, title)

    # Preserve the generated alpha; trim only transparent padding for placement.
    with Image.open(args.mascot) as source:
        mascot = source.convert("RGBA")
        visible = mascot.getchannel("A").point(lambda alpha: 255 if alpha > 32 else 0)
        mascot = mascot.crop(visible.getbbox())
    mascot_ax = fig.add_axes([COMPOSITION_LEFT / CANVAS_WIDTH, 5 / CANVAS_HEIGHT,
                              MASCOT_WIDTH / CANVAS_WIDTH, 32 / CANVAS_HEIGHT], zorder=1)
    mascot_ax.imshow(mascot)
    mascot_ax.set_axis_off()

    # RQ2 input ordering: action prompt, plus sign, then observation.
    input_x = PANEL_X[0]
    ax.add_patch(FancyBboxPatch((input_x + 2.2, 27.8), PANEL_WIDTH - 4, 6.5,
        boxstyle="round,pad=0,rounding_size=3.25", facecolor="#C6A988",
        edgecolor="none", alpha=.18))
    ax.add_patch(FancyBboxPatch((input_x + 2, 28.3), PANEL_WIDTH - 4, 6.5,
        boxstyle="round,pad=0,rounding_size=3.25", facecolor="#FFEBD2",
        edgecolor="#E5B67A", linewidth=.6))
    prompt = textwrap.fill(data["action"], width=24)
    ax.text(input_x + PANEL_WIDTH / 2, 31.55, f'“{prompt}”', ha="center", va="center", fontsize=6.1,
            linespacing=1.2, color=INK)
    ax.text(input_x + PANEL_WIDTH / 2, 26.1, "+", ha="center", va="center",
            fontsize=9, color=INK)
    image_axes(fig, PANEL_X[0], observation, data["observation_view"], inset=True)

    prediction_ax, prediction_clip = image_axes(fig, PANEL_X[1], observation, data["observation_view"])
    draw_predictions(prediction_ax, points)
    evaluation_ax, evaluation_clip = image_axes(fig, PANEL_X[2], observation, data["evaluation_view"])
    # Zoom for legibility; radii stay in the original frame's pixel units.
    for threshold, color in [(.05, LOOSE), (.01, STRICT)]:
        evaluation_ax.add_patch(Circle((gt["x"], gt["y"]), threshold * diagonal,
            facecolor=color, alpha=.12, edgecolor="none", zorder=3))
        evaluation_ax.add_patch(Circle((gt["x"], gt["y"]), threshold * diagonal,
            fill=False, edgecolor=color, linewidth=1.4, zorder=5))
    draw_predictions(evaluation_ax, points, detail=True)
    evaluation_ax.scatter([gt["x"]], [gt["y"]], marker="*", s=45, c="white",
                          edgecolors=INK, linewidths=.8, zorder=9)
    for pane, clip in [(prediction_ax, prediction_clip), (evaluation_ax, evaluation_clip)]:
        for artist in [*pane.patches, *pane.collections, *pane.texts]:
            artist.set_clip_path(clip)
            artist.set_clip_on(True)

    for left, right in zip(PANEL_X, PANEL_X[1:]):
        start, end = left + PANEL_WIDTH + .5, right - .5
        ax.add_patch(FancyArrowPatch((start, 17.5), (end, 17.5), arrowstyle="-|>",
                     mutation_scale=7, lw=.7, color=INK))

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with io.BytesIO() as buffer:
        fig.savefig(buffer, format="png", dpi=OUTPUT_WIDTH / fig.get_figwidth())
        buffer.seek(0)
        rendered = Image.open(buffer).convert("RGB")
        # Avoid backend floating-point rounding changing the aspect ratio.
        rendered = rendered.resize((OUTPUT_WIDTH, OUTPUT_HEIGHT), Image.Resampling.LANCZOS)
        rendered.save(args.output, format="WEBP", quality=95, method=6)
    plt.close(fig)
    print(args.output)


if __name__ == "__main__":
    main()
