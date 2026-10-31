<script lang="ts">
  import PageHead from "#lib/components/PageHead.svelte";
  import SiteNav from "#lib/components/SiteNav.svelte";
  import ProjectHero from "#lib/components/ProjectHero.svelte";
  import ProjectOverview from "#lib/components/ProjectOverview.svelte";
  import Citation from "#lib/components/Citation.svelte";
  import SiteFooter from "#lib/components/SiteFooter.svelte";
  import DatasetSection from "#lib/components/DatasetSection.svelte";
  import ManipulationSection from "#lib/components/ManipulationSection.svelte";
  import BenchmarksSection from "#lib/components/BenchmarksSection.svelte";
</script>

<PageHead />
<SiteNav />
<main id="main-content" class="reading-content" tabindex="-1">
  <ProjectHero />
  <section class="section pt-0">
    <div class="reading-column">
      <ProjectOverview />
      <DatasetSection />
      <BenchmarksSection />
      <ManipulationSection />
    </div>
  </section>
  <Citation />
</main>
<div class="reading-content"><SiteFooter /></div>
