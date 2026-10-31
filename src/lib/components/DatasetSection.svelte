<script lang="ts">
  import { onMount, tick } from "svelte";
  import { replaceState } from "$app/navigation";
  import { page } from "$app/state";
  import TextBlock from "./TextBlock.svelte";
  import SectionHeading from "./SectionHeading.svelte";
  import DatasetExplorer from "./DatasetExplorer.svelte";
  import DatasetDistributions from "./DatasetDistributions.svelte";
  import AnnotationDemo from "./AnnotationDemo.svelte";
  const tabs = [
    {
      id: "dataset-explorer",
      title: "Explore interactions",
      detail: "Real-world contact, through time",
    },
    {
      id: "dataset-statistics",
      title: "Scale & diversity",
      detail: "Objects and actions across the dataset",
    },
    {
      id: "dataset-annotations",
      title: "Annotation precision",
      detail: "From observation to first contact",
    },
  ];
  const defaultTab = "dataset-explorer";
  let active = $state(defaultTab);
  function selectTab(id: string) {
    active = id;
    replaceState(`#${id}`, page.state);
  }
  async function activateHash() {
    const hash = location.hash.slice(1);
    if (tabs.some((tab) => tab.id === hash)) active = hash;
    else if (hash === "spacetime") active = defaultTab;
    else return;
    // Reveal the panel before scrolling to an incoming fragment link.
    await tick();
    if (location.hash.slice(1) === hash)
      document.getElementById(hash)?.scrollIntoView();
  }
  onMount(() => {
    activateHash();
    window.addEventListener("hashchange", activateHash);
    return () => window.removeEventListener("hashchange", activateHash);
  });
  function keydown(event: KeyboardEvent, index: number) {
    let next = index;
    if (event.key === "ArrowRight") next = (index + 1) % tabs.length;
    else if (event.key === "ArrowLeft")
      next = (index + tabs.length - 1) % tabs.length;
    else if (event.key === "Home") next = 0;
    else if (event.key === "End") next = tabs.length - 1;
    else return;
    event.preventDefault();
    selectTab(tabs[next].id);
    document.getElementById(`${active}-tab`)?.focus();
  }
</script>

<section
  id="dataset"
  class="mb-6 mt-6"
  aria-label="EgoContact dataset"
  tabindex="-1"
>
  <SectionHeading title="EgoContact Dataset" />
  <TextBlock
    ><p>
      EgoContact captures <strong>22,523 manually verified interactions</strong> from
      everyday egocentric video sourced from Ego4D. Each event connects an intended
      action to precise contact locations, annotated before and at contact.
    </p></TextBlock
  >
  <div
    class="dataset-tabs"
    role="tablist"
    aria-label="Explore the EgoContact dataset"
  >
    {#each tabs as tab, i}<button
        id={`${tab.id}-tab`}
        role="tab"
        aria-selected={active === tab.id}
        aria-controls={tab.id}
        tabindex={active === tab.id ? 0 : -1}
        class:active={active === tab.id}
        onclick={() => selectTab(tab.id)}
        onkeydown={(event) => keydown(event, i)}
        ><strong>{tab.title}</strong><span>{tab.detail}</span></button
      >{/each}
  </div>
  {#each tabs as tab}
    <div
      id={tab.id}
      role="tabpanel"
      aria-labelledby={`${tab.id}-tab`}
      tabindex="0"
      hidden={active !== tab.id}
    >
      {#if active === tab.id}
        {#if tab.id === "dataset-explorer"}<DatasetExplorer />
        {:else if tab.id === "dataset-statistics"}<DatasetDistributions />
        {:else}<AnnotationDemo />{/if}
      {/if}
    </div>
  {/each}
</section>

<style>
  .dataset-tabs {
    display: grid;
    grid-template-columns: repeat(3, minmax(0, 1fr));
    gap: 0.75rem;
    margin: 2rem 0;
  }
  .dataset-tabs button {
    text-align: left;
    background: white;
    border: 1px solid #ddd;
    border-radius: 0;
    padding: 1.1rem;
    cursor: pointer;
    color: #111;
    font: inherit;
  }
  .dataset-tabs button.active {
    border-color: #111;
    box-shadow: inset 0 -3px #111;
    background: #fafafa;
  }
  strong {
    font-weight: 600;
  }
  .dataset-tabs strong {
    display: block;
    font-size: 0.95rem;
  }
  .dataset-tabs span {
    display: block;
    font-size: 0.75rem;
    color: #666;
    margin-top: 0.4rem;
    line-height: 1.5;
  }
  button:focus-visible,
  [role="tabpanel"]:focus-visible {
    outline: 2px solid #0072b2;
    outline-offset: 4px;
  }
  @media (max-width: 600px) {
    .dataset-tabs {
      gap: 0.4rem;
    }
    .dataset-tabs button {
      padding: 0.7rem 0.5rem;
    }
    .dataset-tabs strong {
      font-size: 0.8rem;
    }
    .dataset-tabs span {
      display: none;
    }
  }
</style>
