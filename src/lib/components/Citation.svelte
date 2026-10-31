<script lang="ts">
  import { citation } from "#lib/data/project.js";
  import SectionHeading from "#lib/components/SectionHeading.svelte";
</script>

<section class="section" id="BibTeX" tabindex="-1" aria-label="Citation">
  <div class="reading-column">
    <SectionHeading title="Citation" />
    <pre class="citation-code"><code>{citation}</code></pre>
  </div>
</section>
