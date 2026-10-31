# EgoContact project page

SvelteKit port of the HiFiEgo / Nerfies project page. Original research content and visual styling are retained for review.

## Local development

```sh
npm install
npm run dev -- --host 127.0.0.1
```

Open http://localhost:5173. For a remote machine, forward the port from your laptop:

```sh
ssh -L 5173:127.0.0.1:5173 your-user@your-server
```

```sh
npm run check
npm run build
npm run preview -- --host 127.0.0.1
```

## Deployment

GitHub Pages is the primary host at https://egocontact.github.io/. The site uses
`@sveltejs/adapter-static` to prerender into `build/`; no base path is needed for
the organization repository `egocontact/egocontact.github.io`.

In the repository's **Settings → Pages → Build and deployment**, set **Source**
to **GitHub Actions**. The workflow in `.github/workflows/deploy.yml` installs
dependencies, checks and builds the site, and deploys `build/` on pushes to
`main`. It can also be started manually from the Actions tab.

Cloudflare Pages can preview the same `main` branch with build command
`npm run build` and output directory `build`. To keep the existing Cloudflare
headers, set its build command to `npm run build && cp _headers build/_headers`.

Components are in `src/lib/components`; shared template styles are in `src/lib/styles/global.css`. Images, dataset map data, and videos live under `static/`.

## License

Website licensed under [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/). Template adapted from [Nerfies](https://github.com/nerfies/nerfies.github.io).

## Asset preparation utilities

The original Python utilities are retained in `utils/` as a separate migration commit. They are offline tools and are not needed to run the website. Their dependencies are separate from the npm dependencies.

The original map selection is retained in `static/data/tsne.json`. It contains
one selected event for each of the 300 most frequent object labels. The t-SNE
layout groups object-label embeddings; it is not a guarantee of scenario or
action diversity. Legacy video links have been removed from this metadata.

## Local data and reference checkouts

Keep datasets under `data/` and external code for review under `tmp/`; both are
ignored by Git, except for `data/.gitkeep`. Set up the local dataset links with:

```sh
mkdir -p data tmp
ln -s ~/storage/user/HIFIEgo/ data/EgoContact
ln -s ~/storage/user/Ego4d/clips data/Ego4D
```

The links are machine-specific and are not committed. `npm run check` selects
the root Vite config explicitly so reference checkouts cannot supply a different
project config.

## Contact-prediction task figure

```sh
/usr/bin/python3 scripts/prepare_contact_prediction_figure.py
```

Requires Matplotlib, NumPy and Pillow. Writes
`static/images/contact-prediction-task.webp`, embedded above the RQ1 table.
The script adapts the original RQ2 `scripts/figure2.py` from
`cppredict/isaac_sim_grasping` (c197c04); its GPLv3 license is retained in
`scripts/LICENSE.figure2`.

The three panels show a cropped observation plus action, five ranked predictions,
and a zoomed evaluation detail. `scripts/assets/contact-prediction-example.json`
records the source event, frame, action and real opposing-finger GT contact.
The rendered reference marker uses an illustrative contact on the mug handle,
stored separately as `display_contact`; the original dataset GT is preserved.
The full 1440×1080 observation is saved alongside it as
`contact-prediction-observation.webp`, so regeneration needs no dataset access.
It is frame 4540 (zero-based) of Ego4D clip
`4c470c78-989f-4331-a1e3-dff778df11b4`, showing the selected “hold mug” example.
The source is recorded in the JSON and comes from
`data/EgoContact/frames/last_observation_frames/`. Crop centers and widths are stored in the example
JSON; they change the viewport without changing annotation coordinates. The input stacks the action prompt, a plus sign, and an inset observation,
matching RQ2. Photos have rounded corners, soft edge shadows, a fine highlight, and a mild
vignette that darkens the photo edges without distorting the scene or annotations.
Dotted panel outlines retain white spacing around the photos. Both figures export at 2400×650.
The three narrower RQ1 stages and mascot are centered together, with equal outer margins.
A smaller project mascot sits to the left of the input, looking toward it and
scratching its head. Its transparent PNG is stored in
`scripts/assets/robot-scratching-head.png` and can be replaced with `--mascot`.

The five predictions are illustrative, not measured model outputs. Evaluation
reuses their exact coordinates. PCK circle radii are computed as 1% and 5% of
the **full-image diagonal**, even though that panel zooms in for readability.

## Experimental spacetime visual

The bottom-of-page `SpacetimeVolume` component uses Three.js to arrange real
video frames through time. It loads near the viewport and renders on interaction,
with no autoplay. At zero intermediate-frame opacity, only the annotated
observation and contact images remain. Solid dots mark annotated endpoints.
Curved lines and hollow inspection markers show optional optical-flow estimates
for this demo, not additional dataset ground truth. The rendering
is an independent implementation inspired by Kosta Derpanis's
[Spacetime Volume](https://csprofkgd.github.io/spacetime-volume/).

Regenerate the compact example assets (requires FFmpeg and the local data links):

```sh
python scripts/prepare_spacetime.py
/usr/bin/python3 scripts/estimate_spacetime_contacts.py
```

The script reads `data/EgoContact/annotations/24_04_2026.json` and a source clip
under `data/Ego4D/`, samples zero-based frame indices from the last prediction
frame through the contact frame (inclusive), and writes JPEGs plus
annotation metadata to `static/data/spacetime/`. Run `--help` for event and path
options. Inputs are read-only. A different event also requires updating the fallback metadata in
`src/lib/data/interaction-example.ts`; the loaded action comes from the manifest.

The optional estimation step requires OpenCV and NumPy. It runs forward pyramidal
Lucas–Kanade on the exported frames, checks each step by tracking backward, and
smoothly corrects endpoint drift to match the final annotation. It writes estimates
and method/error metadata only into the website manifest, plus a labeled montage
in ignored `tmp/visual-qa/contact-tracks.jpg` for manual review. These checks cannot
prove correspondence under occlusion. Re-exporting frames clears the estimates;
rerun estimation afterward. Without estimates, the visual uses straight endpoint
connections. The current cup example has maximum round-trip errors below 0.63 px,
but uncorrected endpoint drift of 10.3/13.2 px at 480×360, so the paths must not be
treated as measured contact trajectories.

## Public release

The public history starts from a single release snapshot. Legacy interaction
MP4s were replaced by WebP explorer frames and are not included in this history.
Only the annotation workflow video remains in `static/videos`.

### Dataset explorer and diversity

The dataset section has three tabs: a searchable single-sample spacetime explorer, the paper's diversity figure, and the annotation workflow video. The explorer uses the prepared cup event in `src/lib/data/interaction-example.ts`; the full dataset is not yet browsable.

The diversity tab preserves the photo mosaic and shows two frequency charts, sorted from most to least frequent, with magma colors for actions and viridis colors for objects. Each chart scrolls horizontally (touch, mouse drag, scrollbar or keyboard) to reveal the long tail while the log-scale axis stays visible. Long labels are truncated; hover a bar for its full label, count and ID. The plotted counts use recorded nonnegative action/object IDs. The original STA taxonomy is still needed to verify display names and assignments.

Regenerate counts and the ID audit with:

```bash
python3 scripts/prepare_dataset_distributions.py
# Once available, verify IDs/names against an STA annotation/taxonomy JSON:
python3 scripts/prepare_dataset_distributions.py --taxonomy /path/to/fho_sta_train.json
```

ID 0 is valid. ID -1 is unmapped; missing or malformed IDs are accounted for separately. The source annotations are never modified. The exporter writes the full ID frequencies to `src/lib/data/dataset-distributions.json` and a provenance hash, per-ID label variants, and event-level review queue to `reports/semantic-audit/`.

### Semantic review

The semantic analysis starts from the original `action`, `object`, and `interaction_description` fields, independently of the generated Ego4D labels. It uses local, attention-masked mean-pooled MiniLM embeddings to retrieve candidates, followed by explicit surface-normalization rules and contextual review. Similarity never automatically merges concepts or rewrites IDs. Opposites, specific motions, materials versus tools, and objects versus parts are retained. The existing coarse ID view and fine-grained phrase view are reported separately; phrase inventories are not class counts.

Use a Python environment with `torch`, `transformers`, and `numpy`:

```bash
python scripts/analyze_semantic_similarity.py --revision 1110a243fdf4706b3f48f1d95db1a4f5529b4d41
python scripts/summarize_semantic_review.py
python3 -m unittest discover -s tests -p 'test_semantic*.py'
```

Open `reports/semantic-audit/report.html` locally to inspect every phrase, its eight nearest neighbors, stored-ID distribution, and example descriptions. `reviewed-analysis.json` includes frequency/entropy metrics, reviewed relationships and event-level judgments. `normalization-overlay.json` records each applied surface normalization without changing original data; `assignment-candidates.csv` lists exact-phrase consistency proposals that have **not** been applied. Some cases need taxonomy verification, and tool/target ambiguities need video/contact review.

The original STA taxonomy remains required for canonical relabeling. The audit does not equate repeated model assignments with ground-truth correctness, and no comparison to another dataset's class count is justified without matching its taxonomy and counting convention.
