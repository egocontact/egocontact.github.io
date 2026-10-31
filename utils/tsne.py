#!/usr/bin/env python3

from __future__ import annotations

import argparse
import json
import random
from collections import Counter
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
import torch
from sentence_transformers import SentenceTransformer
from sklearn.cluster import KMeans
from sklearn.manifold import TSNE


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate t-SNE visualization of HiFiEgo object semantics."
    )
    parser.add_argument("--annotations-json", required=True, help="Path to annotations dict JSON (e.g. annotations_all_15_01_qwen_dict.json).")
    parser.add_argument("--output-json", required=True, help="Path to write tsne_points.json.")
    parser.add_argument("--output-png", required=True, help="Path to write the t-SNE scatter plot PNG.")
    parser.add_argument("--samples-per-noun", type=int, default=1, help="Representative sample IDs to pick per unique noun (default: 1).")
    parser.add_argument("--top-nouns", type=int, default=300, help="Only keep the top-N most frequent nouns (default: 300).")
    parser.add_argument("--n-clusters", type=int, default=10, help="Number of clusters to assign in the t-SNE output JSON (default: 10).")
    parser.add_argument("--seed", type=int, default=42, help="Random seed (default: 42).")
    return parser.parse_args()


def load_records(path: Path) -> list[dict]:
    """Load qwen dict JSON and flatten to list of {sample_id, noun, verb} dicts."""
    print(f"Loading annotations from {path}...")
    with open(path) as f:
        data = json.load(f)

    records = []
    for sample_id, ann in data.items():
        sem = ann.get("semantic_annotation", {})
        if sem:
            noun = sem.get("object", "").split("_")[0].strip().lower() or "unknown"
            verb = sem.get("action", "").strip().lower() or "unknown"
        else:
            # fall back: parse action_label like "pick Plastic cover"
            parts = ann.get("action_label", "unknown unknown").split(None, 1)
            verb = parts[0].lower() if parts else "unknown"
            noun = parts[1].lower() if len(parts) > 1 else "unknown"
        records.append({"sample_id": sample_id, "noun": noun, "verb": verb})
    return records


def generate_embeddings(text_list: list[str], device: str) -> np.ndarray:
    print(f"Using device: {device}")
    print(f"Loading SentenceTransformer model...")
    model = SentenceTransformer("all-MiniLM-L6-v2", device=device)
    print(f"Generating embeddings for {len(text_list)} unique nouns...")
    return model.encode(text_list, show_progress_bar=True)


def run_tsne(embeddings: np.ndarray, perplexity: int = 30, seed: int = 42) -> np.ndarray:
    perplexity = min(perplexity, len(embeddings) - 1)
    print(f"Running t-SNE with perplexity={perplexity}...")
    tsne = TSNE(n_components=2, random_state=seed, perplexity=perplexity, init="pca", learning_rate="auto")
    return tsne.fit_transform(embeddings)


def normalize_coords(xy: np.ndarray) -> np.ndarray:
    """Normalize x, y to [0, 100] range."""
    mn = xy.min(axis=0)
    mx = xy.max(axis=0)
    return (xy - mn) / (mx - mn + 1e-9) * 100.0


def assign_clusters(xy: np.ndarray, n_clusters: int, seed: int) -> np.ndarray:
    n_clusters = max(1, min(n_clusters, len(xy)))
    kmeans = KMeans(n_clusters=n_clusters, random_state=seed, n_init=10)
    return kmeans.fit_predict(xy)


def scale_radii(counts: list[int], min_radius: float = 4.0, max_radius: float = 14.0) -> np.ndarray:
    values = np.log1p(np.asarray(counts, dtype=float))
    if len(values) == 0:
        return np.array([], dtype=float)

    lo = float(values.min())
    hi = float(values.max())
    if np.isclose(lo, hi):
        return np.full(len(values), (min_radius + max_radius) / 2.0, dtype=float)

    return min_radius + (values - lo) / (hi - lo) * (max_radius - min_radius)


def _add_label(x: float, y: float, label: str, fontsize: int = 11) -> None:
    plt.text(
        x, y, str(label),
        fontsize=fontsize,
        alpha=0.9,
        weight="bold",
        horizontalalignment="center",
        verticalalignment="center",
        bbox=dict(boxstyle="round,pad=0.3", fc="white", ec="gray", alpha=0.7),
    )


def plot_tsne(df: pd.DataFrame, output_path: Path, n_labels: int = 35) -> None:
    print("Creating visualization...")
    plt.figure(figsize=(16, 12))
    sns.set_style("white")

    sns.scatterplot(
        data=df,
        x="x", y="y",
        size="log_count",
        sizes=(20, 400),
        hue="x",
        palette="viridis",
        legend=False,
        alpha=0.7,
        edgecolor="black",
    )

    if len(df) > n_labels:
        kmeans = KMeans(n_clusters=n_labels, random_state=42, n_init=10)
        df = df.copy()
        df["cluster"] = kmeans.fit_predict(df[["x", "y"]])
        for i in range(n_labels):
            subset = df[df["cluster"] == i]
            if subset.empty:
                continue
            top = subset.loc[subset["count"].idxmax()]
            if top.label in {"person", "hand", "other", "unknown", "object"}:
                continue
            _add_label(top.x, top.y, top.label)
    else:
        for _, row in df.iterrows():
            if row.label in {"person", "hand", "other", "unknown", "object"}:
                continue
            _add_label(row.x, row.y, row.label, fontsize=9)

    plt.axis("off")
    plt.tight_layout()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    print(f"Saving PNG to {output_path}...")
    plt.savefig(output_path, dpi=300)
    plt.close()
    print("Done!")


def main() -> int:
    args = parse_args()
    rng = random.Random(args.seed)

    records = load_records(Path(args.annotations_json))
    print(f"Loaded {len(records)} records.")

    # Group sample IDs by noun
    noun_to_samples: dict[str, list[str]] = {}
    noun_to_verbs: dict[str, list[str]] = {}
    for rec in records:
        noun_to_samples.setdefault(rec["noun"], []).append(rec["sample_id"])
        noun_to_verbs.setdefault(rec["noun"], []).append(rec["verb"])

    noun_counts = Counter({noun: len(sids) for noun, sids in noun_to_samples.items()})
    print(f"Found {len(noun_counts)} unique nouns total.")

    # Keep only top-N most frequent nouns
    top_nouns = [noun for noun, _ in noun_counts.most_common(args.top_nouns)]
    noun_to_samples = {n: noun_to_samples[n] for n in top_nouns}
    noun_to_verbs = {n: noun_to_verbs[n] for n in top_nouns}
    unique_nouns = top_nouns
    print(f"Using top {len(unique_nouns)} nouns (by frequency).")

    if len(unique_nouns) < 2:
        print("Not enough unique nouns to perform t-SNE.", flush=True)
        return 1

    # Embed and reduce
    device = "cuda" if torch.cuda.is_available() else "cpu"
    embeddings = generate_embeddings(unique_nouns, device)
    tsne_xy = run_tsne(embeddings, seed=args.seed)
    tsne_xy = normalize_coords(tsne_xy)

    noun_clusters = assign_clusters(tsne_xy, n_clusters=args.n_clusters, seed=args.seed)
    noun_radii = scale_radii([noun_counts[noun] for noun in unique_nouns])
    noun_to_meta = {
        noun: {
            "x": round(float(tsne_xy[i, 0]), 4),
            "y": round(float(tsne_xy[i, 1]), 4),
            "r": round(float(noun_radii[i]), 4),
            "cluster": int(noun_clusters[i]),
            "count": int(noun_counts[noun]),
            "log_count": round(float(np.log1p(noun_counts[noun])), 4),
        }
        for i, noun in enumerate(unique_nouns)
    }

    # Pick representative sample IDs per noun
    output_entries = []
    for noun, sample_ids in noun_to_samples.items():
        rng.shuffle(sample_ids)
        chosen = sample_ids[: args.samples_per_noun]
        meta = noun_to_meta[noun]
        # Most common verb for this noun as a representative label
        verb = Counter(noun_to_verbs[noun]).most_common(1)[0][0]
        for sid in chosen:
            output_entries.append({
                "id": sid,
                "label": noun,
                "verb": verb,
                "noun": noun,
                "x": meta["x"],
                "y": meta["y"],
                "r": meta["r"],
                "cluster": meta["cluster"],
                "count": meta["count"],
                "log_count": meta["log_count"],
            })

    # Write JSON
    output_json = Path(args.output_json)
    output_json.parent.mkdir(parents=True, exist_ok=True)
    with open(output_json, "w") as f:
        json.dump(output_entries, f, indent=2)
    print(f"Wrote {len(output_entries)} entries to {output_json}.")

    # Build dataframe for PNG
    df_tsne = pd.DataFrame({
        "x": [tsne_xy[i, 0] for i in range(len(unique_nouns))],
        "y": [tsne_xy[i, 1] for i in range(len(unique_nouns))],
        "label": unique_nouns,
        "count": [noun_counts[n] for n in unique_nouns],
        "log_count": [np.log1p(noun_counts[n]) for n in unique_nouns],
    })
    plot_tsne(df_tsne, Path(args.output_png))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
