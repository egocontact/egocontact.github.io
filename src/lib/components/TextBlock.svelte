<script lang="ts">
  import type { Snippet } from "svelte";

  let {
    children,
    abstract = false,
  }: { children: Snippet; abstract?: boolean } = $props();
</script>

<div class="text-block" class:abstract>
  {@render children()}
</div>

<style>
  .text-block {
    width: 100%;
    margin: 0 0 1.5rem;
    font-family: var(--font-body);
    font-size: 1rem;
    line-height: 1.5;
    text-align: justify;
  }
  .text-block :global(p) {
    margin: 0;
  }
  .text-block :global(p + p) {
    margin-top: 1em;
  }
  .abstract {
    font-size: 1.1rem;
    line-height: 1.7;
  }
  @media (max-width: 600px) {
    .text-block {
      text-align: left;
    }
    .abstract {
      font-size: 1rem;
    }
  }
</style>
