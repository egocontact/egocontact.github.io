<script lang="ts">
  import { onMount } from "svelte";
  import { assertManifest, type Manifest } from "#lib/data/spacetime.js";
  import { interactionExample } from "#lib/data/interaction-example.js";
  import type { ExplorerSample } from "#lib/data/explorer.js";

  // The parent keys this component by sample ID to dispose the previous scene.
  let { sample = interactionExample }: { sample?: ExplorerSample } = $props();

  let host: HTMLDivElement;
  let data = $state<Manifest | null>(null);
  let ready = $state(false);
  let error = $state("");
  let opacity = $state(12);
  let slice = $state(0);
  let scene:
    | Awaited<ReturnType<typeof import("./spacetime-scene").createScene>>
    | undefined;
  const current = $derived(data?.frames[slice]);
  const time = $derived(
    data && current
      ? ((current.index - data.contact) / data.fps).toFixed(2)
      : "",
  );

  onMount(() => {
    let cancelled = false;
    const controller = new AbortController();
    // Load the 3D code and images only when this experiment approaches view.
    const observer = new IntersectionObserver(
      async (entries) => {
        if (!entries.some((entry) => entry.isIntersecting)) return;
        observer.disconnect();
        try {
          const [module, response] = await Promise.all([
            import("./spacetime-scene"),
            fetch(sample.manifestUrl, {
              signal: controller.signal,
            }),
          ]);
          if (!response.ok) throw new Error("The example could not be loaded.");
          const manifest: Manifest = await response.json();
          if (cancelled) return;
          assertManifest(manifest);
          data = manifest;
          slice = manifest.frames.findIndex(
            (frame) => frame.index === manifest.observation,
          );
          const instance = await module.createScene(host, manifest);
          if (cancelled) {
            instance.dispose();
            return;
          }
          scene = instance;
          ready = true;
        } catch (reason) {
          if (!cancelled)
            error =
              reason instanceof Error
                ? reason.message
                : "3D is unavailable in this browser.";
        }
      },
      { rootMargin: "200px" },
    );
    observer.observe(host);
    return () => {
      cancelled = true;
      controller.abort();
      observer.disconnect();
      scene?.dispose();
    };
  });
</script>

<section
  id="spacetime"
  class="spacetime-experiment"
  aria-labelledby="spacetime-title"
  tabindex="-1"
>
  <div class="viewer-heading">
    <h3 id="spacetime-title">{data?.action ?? sample.action}</h3>
    <div class="view-actions" role="group" aria-label="View controls">
      <button
        disabled={!ready}
        aria-label="Zoom out"
        title="Zoom out"
        onclick={() => scene?.zoom(1.2)}>−</button
      >
      <button
        disabled={!ready}
        aria-label="Zoom in"
        title="Zoom in"
        onclick={() => scene?.zoom(1 / 1.2)}>+</button
      >
      <button
        disabled={!ready}
        onclick={() => {
          opacity = 12;
          slice = data!.frames.findIndex(
            (frame) => frame.index === data!.observation,
          );
          scene?.setOpacity(0.12);
          scene?.setSlice(slice);
          scene?.resetView();
        }}>Reset view</button
      >
    </div>
  </div>
  <figure>
    <div class="volume-stage">
      <div class="stage-heading" aria-hidden="true">
        <span><i class="observation"></i>Pre-contact observation</span>
        <span><i class="contact"></i>First contact</span>
      </div>
      <div class="volume-canvas" bind:this={host}></div>
      {#if !ready}
        <div class="fallback">
          {#each sample.frames as frame}
            <div>
              <img src={frame.src} alt={frame.description} /><span
                >{frame.label}</span
              >
            </div>
          {/each}
          <p role="status">{error || "Preparing the interaction volume…"}</p>
        </div>
      {/if}
      <div class="stage-footer">
        <div class="contact-legend" aria-label="Contact legend">
          <span><i class="thumb"></i>Thumb</span>
          <span><i class="finger"></i>Opposing finger</span>
        </div>
        <span class="stage-hint"
          >Drag to rotate · Pinch / Ctrl + scroll to zoom</span
        >
      </div>
    </div>
    <div class="volume-controls">
      <div class="slider-row">
        <label for="volume-opacity">Frame opacity</label>
        <input
          id="volume-opacity"
          type="range"
          min="0"
          max="35"
          step="1"
          bind:value={opacity}
          disabled={!ready}
          oninput={() => scene?.setOpacity(opacity / 100)}
        />
        <output for="volume-opacity">{opacity}%</output>
      </div>
      <div class="slider-row">
        <label for="volume-time">Time</label>
        <input
          id="volume-time"
          type="range"
          min="0"
          max={data ? data.frames.length - 1 : 1}
          step="1"
          bind:value={slice}
          disabled={!ready || opacity === 0}
          oninput={() => scene?.setSlice(slice)}
          aria-valuetext={`${time} seconds relative to contact`}
        />
        <output for="volume-time">{ready ? `${time} s` : "—"}</output>
      </div>
    </div>
  </figure>
</section>

<style>
  .spacetime-experiment {
    container-type: inline-size;
    max-width: calc(var(--reading-width) + 2.5rem);
    margin: 1.5rem auto 0;
    padding: 0;
  }
  .viewer-heading {
    display: flex;
    flex-wrap: wrap;
    align-items: center;
    justify-content: space-between;
    gap: 1rem;
    margin-bottom: 0.65rem;
  }
  .viewer-heading h3 {
    flex: 1 1 200px;
  }
  .view-actions {
    display: flex;
    gap: 0.4rem;
    flex-shrink: 0;
  }
  .view-actions button {
    min-width: 36px;
    min-height: 36px;
  }
  .viewer-heading button {
    flex-shrink: 0;
  }
  h3 {
    margin: 0;
    font-size: 1.15rem;
    font-weight: 650;
    color: #111;
    line-height: 1.2;
  }
  figure {
    margin: 0;
  }
  .volume-stage {
    position: relative;
    height: clamp(340px, 55svh, 520px);
    border-radius: 0;
    overflow: hidden;
    background: #000;
    border: 1px solid #111;
    border-bottom: 0;
  }
  .volume-canvas {
    position: absolute;
    inset: 0;
  }
  .volume-canvas :global(canvas) {
    display: block;
    width: 100%;
    height: 100%;
    touch-action: pan-y;
  }
  .stage-heading {
    position: absolute;
    top: 22px;
    left: 24px;
    right: 24px;
    display: flex;
    justify-content: space-between;
    gap: 1rem;
    color: #eee;
    font-size: 0.75rem;
    pointer-events: none;
    z-index: 1;
  }
  i {
    display: inline-block;
    width: 8px;
    height: 8px;
    border-radius: 50%;
    margin-right: 7px;
  }
  .observation {
    background: #fff;
  }
  .contact {
    background: #888;
  }
  .thumb {
    background: #39baff;
  }
  .finger {
    background: #f36ac4;
  }
  .stage-footer {
    position: absolute;
    bottom: 14px;
    left: 16px;
    right: 16px;
    display: flex;
    flex-wrap: wrap;
    align-items: center;
    justify-content: space-between;
    gap: 12px;
    color: #eee;
    pointer-events: none;
  }
  .stage-hint {
    font-size: 0.65rem;
    color: #aaa;
  }
  .volume-controls {
    display: grid;
    grid-template-columns: repeat(2, minmax(0, 1fr));
    align-items: center;
    gap: 20px;
    background: #fafafa;
    padding: 12px 16px;
    border: 1px solid #ddd;
    color: #333;
  }
  .slider-row {
    display: grid;
    grid-template-columns: minmax(0, 1fr) auto;
    align-items: center;
    gap: 4px 8px;
    font-size: 0.72rem;
  }
  .slider-row label {
    grid-column: 1;
    grid-row: 1;
  }
  .slider-row output {
    grid-column: 2;
    grid-row: 1;
  }
  .slider-row input {
    grid-column: 1 / -1;
    grid-row: 2;
    margin: 0;
    min-width: 0;
  }
  input {
    width: 100%;
    accent-color: #111;
    cursor: pointer;
  }
  output {
    text-align: right;
    font-variant-numeric: tabular-nums;
    color: #555;
  }
  .contact-legend {
    display: flex;
    gap: 18px;
    font-size: 0.65rem;
  }
  button {
    background: #111;
    color: #fff;
    border: 1px solid #111;
    border-radius: 0;
    padding: 7px 11px;
    cursor: pointer;
    font: inherit;
    font-size: 0.73rem;
  }
  button:hover {
    background: #333;
  }
  button:disabled {
    opacity: 0.45;
    cursor: default;
  }
  button:focus-visible,
  input:focus-visible {
    outline: 2px solid #111;
    outline-offset: 4px;
  }
  .fallback {
    position: absolute;
    inset: 65px 24px;
    display: flex;
    flex-wrap: wrap;
    align-content: center;
    justify-content: center;
    gap: 18px;
    color: #eee;
    text-align: center;
    pointer-events: none;
  }
  .fallback div {
    width: 40%;
  }
  .fallback img {
    width: 100%;
    max-height: 270px;
    object-fit: contain;
  }
  .fallback span {
    display: block;
    font-size: 0.75rem;
  }
  .fallback p {
    width: 100%;
    font-size: 0.8rem;
  }
  @container (max-width: 420px) {
    .volume-stage {
      height: clamp(300px, 48svh, 420px);
    }
    .volume-controls {
      gap: 10px;
      padding: 10px;
    }
    .slider-row {
      font-size: 0.65rem;
    }
    button {
      padding: 6px;
      font-size: 0.65rem;
    }
    .stage-heading {
      font-size: 0.6rem;
      left: 12px;
      right: 12px;
    }
    .contact-legend {
      gap: 10px;
      font-size: 0.6rem;
    }
    .stage-hint {
      font-size: 0.6rem;
    }
  }
</style>
