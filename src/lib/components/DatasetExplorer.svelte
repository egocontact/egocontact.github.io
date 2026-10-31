<script lang="ts">
  import SpacetimeVolume from "./SpacetimeVolume.svelte";
  import samples from "#lib/data/explorer-samples.json";
  import type { ExplorerSample } from "#lib/data/explorer.js";
  const searchable = samples.map((sample) => ({
    sample,
    text: [sample.object, sample.verb, sample.action, sample.id]
      .join(" ")
      .toLowerCase(),
  }));
  let query = $state("");
  let selected = $state<ExplorerSample>(samples[0]);
  let sampleList: HTMLDivElement;
  const words = $derived(query.trim().toLowerCase().split(/\s+/));
  const matches = $derived(
    searchable.filter(({ text }) => words.every((word) => text.includes(word))),
  );
  function shortId(id: string) {
    const [clip, frame] = id.split("_");
    return `${clip.slice(0, 8)}…_${frame}`;
  }
</script>

<div class="explorer">
  <aside class="sample-browser" aria-label="Sample browser">
    <div class="browser-heading">
      <h3>Samples</h3>
    </div>
    <label
      >Search samples<input
        type="search"
        bind:value={query}
        oninput={() => (sampleList.scrollTop = 0)}
        placeholder="Object, action, ID…"
      /></label
    >
    <p class="sample-count" role="status">
      {matches.length} of {samples.length} samples
    </p>
    <div class="sample-list" bind:this={sampleList}>
      {#each matches as { sample } (sample.id)}
        <button
          class="sample"
          class:selected={selected.id === sample.id}
          aria-pressed={selected.id === sample.id}
          aria-controls="active-sample"
          aria-label={`Sample ${sample.id}: ${sample.verb} ${sample.object}`}
          onclick={() => (selected = sample)}
        >
          <img
            src={sample.frames[0].src}
            alt=""
            loading="lazy"
            width="56"
            height="56"
          />
          <span class="sample-detail">
            <strong class="sample-id" title={sample.id}
              >{shortId(sample.id)}</strong
            >
            <span class="sample-tags">
              <span class="sample-tag" title={`Action: ${sample.verb}`}
                >{sample.verb}</span
              >
              <span class="sample-tag" title={`Object: ${sample.object}`}
                >{sample.object}</span
              >
            </span>
          </span>
        </button>
      {/each}
      {#if !matches.length}
        <div class="empty">
          <p>No samples match “{query}”.</p>
          <button
            class="clear"
            onclick={() => {
              query = "";
              sampleList.scrollTop = 0;
            }}>Clear search</button
          >
        </div>
      {/if}
    </div>
  </aside>
  <div
    id="active-sample"
    class="sample-viewer"
    tabindex="-1"
    aria-label="Active sample"
  >
    {#key selected.id}
      <SpacetimeVolume sample={selected} />
    {/key}
    {#if !matches.some(({ sample }) => sample.id === selected.id)}
      <p class="selection-note">
        The selected sample is outside the current search results.
      </p>
    {/if}
  </div>
</div>

<style>
  .explorer {
    display: grid;
    grid-template-columns: 280px minmax(0, 1fr);
    border: 1px solid #ddd;
    border-radius: 0;
    overflow: hidden;
    align-items: stretch;
  }
  .sample-browser {
    display: flex;
    flex-direction: column;
    padding: 1.1rem 0.85rem;
    background: #fafafa;
    border-right: 1px solid #ddd;
    min-width: 0;
    min-height: 0;
  }
  .browser-heading {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 0.5rem;
    margin-bottom: 1.25rem;
  }
  h3 {
    font-size: 0.95rem;
    font-weight: 600;
    color: #111;
  }
  label {
    display: grid;
    gap: 0.4rem;
    font-size: 0.75rem;
  }
  input {
    font: inherit;
    font-size: 0.8rem;
    padding: 0.65rem 0.6rem;
    border: 1px solid #ccc;
    border-radius: 0;
    width: 100%;
    min-width: 0;
    background: white;
    color: #111;
  }
  .sample-count {
    font-size: 0.7rem;
    color: #777;
    margin: 1rem 0 0.6rem;
  }
  .sample {
    display: flex;
    width: 100%;
    align-items: center;
    gap: 0.65rem;
    padding: 0.65rem;
    border: 1px solid transparent;
    border-left: 3px solid transparent;
    border-bottom-color: #e2e2e2;
    border-radius: 0;
    background: transparent;
    text-align: left;
    cursor: pointer;
    font: inherit;
  }
  .sample:hover {
    background: #eee;
  }
  .sample.selected {
    background: #edf1f4;
    border-left-color: #111;
  }
  .sample-list {
    flex: 1 1 0;
    min-height: 0;
    height: 0;
    overflow-y: auto;
    overscroll-behavior: contain;
  }
  img {
    width: 56px;
    height: 56px;
    flex-shrink: 0;
    object-fit: cover;
    border-radius: 0;
  }
  .sample-detail {
    min-width: 0;
  }
  .sample-id {
    display: block;
    font-family: var(--font-mono, monospace);
    font-size: 0.68rem;
    font-weight: 600;
    color: #111;
    overflow-wrap: anywhere;
  }
  .sample-tags {
    display: flex;
    flex-wrap: wrap;
    gap: 0.3rem;
    margin-top: 0.45rem;
  }
  .sample-tag {
    padding: 0.2rem 0.35rem;
    border: 1px solid #ddd;
    border-radius: 3px;
    background: white;
    color: #333;
    font-size: 0.62rem;
    font-weight: 600;
    line-height: 1.35;
    text-transform: uppercase;
    overflow-wrap: anywhere;
    min-width: 0;
  }
  .selection-note {
    margin-top: 0.75rem;
    font-size: 0.7rem;
    line-height: 1.5;
    color: #666;
  }
  .sample-viewer {
    min-width: 0;
    padding: 1.25rem;
    background: white;
  }
  .sample-viewer :global(.spacetime-experiment) {
    margin: 0;
  }
  .empty {
    padding: 1rem 0;
    font-size: 0.8rem;
    overflow-wrap: anywhere;
  }
  .clear {
    margin-top: 0.75rem;
    border: 1px solid #ccc;
    border-radius: 0;
    padding: 0.4rem 0.6rem;
    background: white;
    cursor: pointer;
    font: inherit;
  }
  input:focus-visible,
  button:focus-visible,
  .sample-viewer:focus-visible {
    outline: 2px solid #111;
    outline-offset: 3px;
  }
  @media (min-width: 1100px) {
    .explorer {
      --explorer-overhang: clamp(
        0px,
        calc(
          (100vw - var(--reading-sidebar-width) - var(--reading-width) - 3rem) /
            2
        ),
        6rem
      );
      margin-inline: calc(-1 * var(--explorer-overhang));
    }
  }
  @media (max-width: 700px) {
    .sample-list {
      flex: 0 1 auto;
      height: auto;
      max-height: 160px;
    }
    .explorer {
      grid-template-columns: minmax(0, 1fr);
    }
    .sample-browser {
      border-right: 0;
      border-bottom: 1px solid #ddd;
    }
    .browser-heading {
      margin-bottom: 0.75rem;
    }
    .sample-viewer {
      padding: 1rem 0.65rem;
    }
  }
</style>
