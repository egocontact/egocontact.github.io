<script lang="ts">
  import TextBlock from "#lib/components/TextBlock.svelte";
  import SectionHeading from "#lib/components/SectionHeading.svelte";
  import { benchmarks } from "#lib/data/benchmarks.js";
  import BenchmarkTable from "#lib/components/BenchmarkTable.svelte";
</script>

<section
  id="contact-prediction"
  class="mb-6 mt-6"
  aria-label="Research question 1"
  tabindex="-1"
>
  <SectionHeading
    title="RQ1: Do current models possess physically precise affordance understanding?"
  />
  <section id="contact-setup" aria-labelledby="contact-setup-heading" tabindex="-1">
    <h3 id="contact-setup-heading" class="subsection-heading">Experimental setup</h3>
    <TextBlock>
      <p>
        Given an image before contact and an intended action, where would a model
        interact with the object? We compare its predictions with the contact
        observed in the subsequent human interaction. Each candidate predicts the
        same opposing-finger contact; Top-1 and Top-5 evaluate the best match
        among one or five ranked alternatives.
      </p>
      <p>
        We evaluate affordance grounding, affordance transfer, and vision-language
        models. The metrics distinguish two challenges: finding the target object
        and placing a precise contact on it.
      </p>
    </TextBlock>
    <figure class="task-figure">
      <img
        src="/images/contact-prediction-task.webp"
        width="2400"
        height="650"
        loading="lazy"
        alt="A puzzled robot mascot scratches its head while looking at the contact prediction task: a cropped pre-contact view of a mug in a dish rack and the action hold mug; five illustrative ranked contact predictions; then a contact detail comparing those same predictions with an illustrative reference contact on the mug handle and tolerance circles at 1% and 5% of the full-frame diagonal."
      />
    </figure>
  </section>

  <section id="contact-results" aria-labelledby="contact-results-heading" tabindex="-1">
    <h3 id="contact-results-heading" class="subsection-heading">Results</h3>
    <BenchmarkTable benchmark={benchmarks[0]} />
    <TextBlock>
      <p>
        <strong>Finding the object is only the first step.</strong> Predictions often
        miss the target object entirely, and even correctly localized predictions struggle
        at fine contact precision. Muse Spark 1.3 reaches 79.91% Top-5 object localization,
        but only 11.05% contact accuracy at the strict 1% threshold.
      </p>
      <p>
        At the looser 5% threshold, no evaluated model surpasses the 73.78%
        accuracy of the ground-truth bounding-box center. This oracle baseline
        shows why coarse localization alone can score well without capturing the
        precise contact observed in a human interaction.
      </p>
    </TextBlock>
  </section>
</section>

<style>
  .subsection-heading {
    font-size: 1.15rem;
    font-weight: 600;
    color: #111;
    margin: 2rem 0 1rem;
  }
  .task-figure {
    margin: 0;
  }
  .task-figure img {
    display: block;
    width: 100%;
    height: auto;
  }
</style>
