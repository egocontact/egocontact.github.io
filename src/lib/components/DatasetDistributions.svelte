<script lang="ts">
  import { interpolateMagma, interpolateViridis } from "d3";
  import distribution from "#lib/data/dataset-distributions.json";
  import tiles from "#lib/data/diversity-mosaic.json";
  const ticks = [1, 10, 100, 1000, 10000];
  const baseline = 160;
  const step = 24;
  // Keep the first rotated label inside the scrollable SVG viewport.
  const plotInset = 16;
  const labelLimit = 10;
  const shortLabel = (label: string) => label.length > labelLimit
    ? `${label.slice(0, labelLimit - 1).trimEnd()}…`
    : label;
  const y = (count: number) => baseline - Math.log10(count / 0.8) / Math.log10(20000 / 0.8) * 140;
  const panels = distribution.panels.map((panel) => ({
    ...panel,
    chartHeight: baseline + 20 + Math.ceil(Math.max(
      ...panel.groups.flatMap((group) => group.rows.map((row) => shortLabel(row.label).length)),
    ) * 5.2 * Math.sin(65 * Math.PI / 180)),
    rows: panel.groups.flatMap((group) => group.rows.map((row) => ({
      ...row,
      group: group.title,
    }))).sort((a, b) => b.count - a.count || a.id - b.id)
      .map((row, index, rows) => ({
        ...row,
        color: (panel.key === "actions" ? interpolateMagma : interpolateViridis)(
          0.12 + 0.73 * index / Math.max(1, rows.length - 1),
        ),
      })),
  }));
  let drag: { id: number; x: number; left: number } | null = null;
  function startDrag(event: PointerEvent & { currentTarget: HTMLDivElement }) {
    if (event.pointerType !== "mouse" || event.button !== 0) return;
    drag = { id: event.pointerId, x: event.clientX, left: event.currentTarget.scrollLeft };
    event.currentTarget.setPointerCapture(event.pointerId);
  }
  function moveDrag(event: PointerEvent & { currentTarget: HTMLDivElement }) {
    if (drag?.id === event.pointerId) {
      event.currentTarget.scrollLeft = drag.left + drag.x - event.clientX;
    }
  }
  function endDrag() { drag = null; }
</script>

<figure class="diversity-figure">
  <div
    class="mosaic"
    role="img"
    aria-label="A dense grid of 80 real egocentric frames illustrating the variety of EgoContact's 22,523 interactions"
  >
    <div class="photo-grid" aria-hidden="true">
      {#each tiles as tile}<div
          class="tile"
          style:background-position={`${(tile.column / 63) * 100}% ${(tile.row / 74) * 100}%`}
        ></div>{/each}
    </div>
    <div class="mosaic-title" aria-hidden="true">
      <strong>22,523</strong><span>human–object interactions</span>
    </div>
  </div>
  {#each panels as panel}
    <section class="distribution-panel" aria-label={`${panel.title} frequencies`}>
      <div class="panel-heading">
        <div class="panel-title"><h3>{panel.title}</h3><span class="label-count">{panel.rows.length} labels</span></div>
        <span class="axis-note">Events · log scale</span>
      </div>
      <div class="chart-layout">
        <svg class="y-axis" height={panel.chartHeight} viewBox={`0 0 44 ${panel.chartHeight}`} aria-hidden="true">
          {#each ticks as tick}
            <text x="36" y={y(tick) + 4} text-anchor="end">{tick >= 1000 ? `${tick / 1000}k` : tick}</text>
          {/each}
        </svg>
        <!-- Keyboard focus enables native arrow-key scrolling through the long tail. -->
        <!-- svelte-ignore a11y_no_noninteractive_tabindex -->
        <div class="chart-scroll" tabindex="0" role="region"
          aria-label={`${panel.title}: use arrow keys, swipe, or drag left to see less frequent labels`}
          onpointerdown={startDrag} onpointermove={moveDrag}
          onpointerup={endDrag} onpointercancel={endDrag} onlostpointercapture={endDrag}>
          <svg class="bars" width={plotInset + panel.rows.length * step + 12} height={panel.chartHeight}
            viewBox={`0 0 ${plotInset + panel.rows.length * step + 12} ${panel.chartHeight}`}
            role="img" aria-label={`${panel.title} frequencies, from most to least frequent`}>
            {#each ticks as tick}
              <line x1="0" x2={plotInset + panel.rows.length * step + 12} y1={y(tick)} y2={y(tick)} class="gridline" />
            {/each}
            <line x1="0" x2={plotInset + panel.rows.length * step + 12} y1={baseline} y2={baseline} class="baseline" />
            {#each panel.rows as row, i}
              <g class="bar" style:--bar-color={row.color}>
                <title>{row.label}: {row.count.toLocaleString()} events · {row.group} (ID {row.id})</title>
                <rect x={plotInset + i * step + 4} y={y(row.count)} width="16" height={baseline - y(row.count)} rx="2" />
                <text class="bar-label" aria-label={row.label} transform={`translate(${plotInset + i * step + 22},171) rotate(-65)`} text-anchor="end">{shortLabel(row.label)}</text>
              </g>
            {/each}
          </svg>
        </div>
      </div>
    </section>
  {/each}
  <figcaption>Most frequent first. Swipe or drag left to explore the long tail.</figcaption>
</figure>

<style>
  .diversity-figure {
    margin: 0;
    color: #111;
  }
  .mosaic {
    position: relative;
    overflow: hidden;
    background: #111;
  }
  .photo-grid {
    display: grid;
    grid-template-columns: repeat(16, minmax(0, 1fr));
    gap: 1px;
  }
  .tile {
    aspect-ratio: 1;
    background-image: url("/images/diversity-atlas.webp");
    background-size: 6400% 7500%;
  }
  .mosaic::after {
    content: "";
    position: absolute;
    inset: 0;
    background: radial-gradient(
      ellipse at center,
      rgba(0, 0, 0, 0.68),
      rgba(0, 0, 0, 0.12) 70%
    );
    pointer-events: none;
  }
  .mosaic-title {
    position: absolute;
    inset: 0;
    display: flex;
    flex-direction: column;
    justify-content: center;
    align-items: center;
    color: #fff;
    z-index: 1;
    text-shadow: 0 1px 8px #0008;
  }
  .mosaic-title strong {
    color: #fff;
    font-size: clamp(2.5rem, 5vw, 4rem);
    font-weight: 600;
    line-height: 1;
    letter-spacing: -0.04em;
  }
  .mosaic-title span {
    font-size: 0.8rem;
    margin-top: 0.6rem;
  }
  .distribution-panel {
    margin-top: 0.4rem;
  }
  .panel-heading {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 1rem;
    padding: 0.45rem 0.65rem;
    background: var(--paper-ink);
    color: #fff;
  }
  .panel-title { display: flex; align-items: center; gap: 0.7rem; }
  h3 {
    font-family: var(--font-body);
    font-size: 0.9rem;
    font-weight: 400;
    line-height: 1.25;
    margin: 0;
    color: #fff;
  }
  .label-count { font-size: 0.72rem; color: #fff; }
  .axis-note { font-size: 0.65rem; color: #fff; }
  .chart-layout {
    display: grid;
    grid-template-columns: 44px minmax(0, 1fr);
    margin-top: 0.35rem;
    padding: 0.25rem 0.25rem 0;
    border: 2px dashed #999;
    border-radius: 10px;
  }
  .y-axis { width: 44px; }
  .chart-scroll {
    overflow-x: auto;
    min-width: 0;
    cursor: grab;
    user-select: none;
    scrollbar-color: #bbb #f2f2f2;
    scrollbar-width: thin;
  }
  .chart-scroll:active { cursor: grabbing; }
  .chart-scroll:focus-visible { outline: 2px solid #555; outline-offset: 3px; }
  .bars { display: block; max-width: none; }
  text { font-family: var(--font-body); font-size: 11px; fill: #777; }
  .bar-label { font-size: 10px; fill: #444; }
  .gridline { stroke: #e8e8e8; stroke-width: 0.7; stroke-dasharray: 3 4; }
  .baseline { stroke: #ccc; stroke-width: 1; }
  .bar rect { fill: var(--bar-color); }
  .bar:hover rect { filter: brightness(0.85); }
  .bar:hover text { fill: #111; }
  figcaption { font-size: 0.7rem; color: #777; margin-top: 0.8rem; }
  @media (max-width: 700px) {
    .photo-grid {
      grid-template-columns: repeat(10, minmax(0, 1fr));
    }
    .mosaic-title strong {
      font-size: 2.5rem;
    }
  }
</style>
