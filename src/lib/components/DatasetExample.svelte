<script lang="ts">
  import { interactionExample } from "#lib/data/interaction-example.js";
  const { frames } = interactionExample;
</script>

<figure
  id="contact-annotation-example"
  class="dataset-example"
  tabindex="-1"
  aria-label="Contact annotations"
>
  <p class="example-action">
    Intended action: <strong>{interactionExample.action}</strong>
  </p>
  <div class="example-frames">
    {#each frames as frame}
      <div>
        <h3 class="title is-5 has-text-centered">{frame.label}</h3>
        <svg
          viewBox="317 378 720 648"
          role="img"
          aria-label={frame.description}
        >
          <image href={frame.src} width="1440" height="1080" />
          {#if frame.box}
            <polygon
              points={frame.box}
              fill="none"
              stroke="white"
              stroke-width="3"
              stroke-dasharray="10 7"
            />
          {/if}
          <circle
            cx={frame.thumb.x}
            cy={frame.thumb.y}
            r="11"
            class="thumb-contact"
          />
          <circle
            cx={frame.finger.x}
            cy={frame.finger.y}
            r="11"
            class="finger-contact"
          />
        </svg>
      </div>
    {/each}
  </div>
  <div class="example-legend" aria-label="Annotation legend">
    <span
      ><span class="legend-dot thumb-contact" aria-hidden="true"></span>Thumb
      contact</span
    >
    <span
      ><span class="legend-dot finger-contact" aria-hidden="true"
      ></span>Opposing-finger contact</span
    >
    <span
      ><span class="legend-box" aria-hidden="true"></span>Target-object box</span
    >
  </div>
  <figcaption class="figure-caption">
    Each example pairs a pre-contact observation with an action description, a
    target-object bounding box, and two precise contact locations. Annotators
    identify the contacts in the subsequent human interaction and mark their
    corresponding locations in the pre-contact image. These annotations provide
    the reference for evaluating predictions made before contact.
  </figcaption>
</figure>

<style>
  .dataset-example {
    margin: 2rem 0;
  }
  .example-action {
    text-align: center;
    margin-bottom: 1.5rem;
  }
  .example-frames {
    max-width: 52rem;
    margin: 0 auto;
    display: grid;
    grid-template-columns: repeat(2, minmax(0, 1fr));
    gap: 1.5rem;
  }
  .example-frames h3 {
    margin-bottom: 0.75rem;
  }
  svg {
    display: block;
    width: 100%;
    height: auto;
  }
  circle {
    stroke: #202020;
    stroke-width: 2;
  }
  .thumb-contact {
    fill: #0072b2;
    background: #0072b2;
  }
  .finger-contact {
    fill: #b23a8a;
    background: #b23a8a;
  }
  .example-legend {
    display: flex;
    flex-wrap: wrap;
    justify-content: center;
    gap: 0.5rem 1.25rem;
    margin: 1rem 0;
    font-size: 0.875rem;
  }
  .example-legend > span {
    display: inline-flex;
    align-items: center;
    gap: 0.4rem;
  }
  .legend-dot {
    width: 0.65rem;
    height: 0.65rem;
    border: 1px solid #202020;
    border-radius: 50%;
  }
  .legend-box {
    width: 0.9rem;
    height: 0.65rem;
    border: 1px dashed #4a4a4a;
  }
  @media (max-width: 600px) {
    .example-frames {
      grid-template-columns: 1fr;
      gap: 1.5rem;
    }
  }
</style>
