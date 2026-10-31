<script lang="ts">
  import { title, authors, affiliations, paperUrl } from "#lib/data/project.js";
  const resources = [
    { label: "Paper", icon: "ai ai-arxiv", href: paperUrl },
    { label: "Code", icon: "fab fa-github", href: null },
    { label: "Data", icon: "fas fa-database", href: null },
  ];
</script>

<section
  id="overview"
  class="hero hero-section"
  tabindex="-1"
  aria-label="Paper overview"
>
  <div class="hero-body">
    <div class="reading-column has-text-centered">
      <h1 class="title is-1 publication-title">{title}</h1>
      <div class="publication-authors">
        {#each authors as author, index}
          <span class="author-block"
            ><a href={author.url}>{author.name}</a><sup
              >{author.affiliations.join(",")}</sup
            >{index < authors.length - 1 ? "," : ""}</span
          >
        {/each}
      </div>
      <div class="publication-affiliations">
        {#each affiliations as affiliation}
          <span class="author-block"
            ><sup>{affiliation.id}</sup>{affiliation.name}</span
          >
        {/each}
      </div>
      <div class="publication-links">
        {#each resources as resource}
          {#if resource.href}
            <a
              class="external-link button is-normal is-rounded is-dark"
              href={resource.href}
            >
              <span class="icon"
                ><i class={resource.icon} aria-hidden="true"></i></span
              >
              <span class="resource-label">{resource.label}</span>
            </a>
          {:else}
            <button
              class="external-link button is-normal is-rounded is-dark"
              type="button"
              disabled
            >
              <span class="icon"
                ><i class={resource.icon} aria-hidden="true"></i></span
              >
              <span class="resource-label"
                >{resource.label}<small>Coming soon</small></span
              >
            </button>
          {/if}
        {/each}
      </div>
    </div>
  </div>
</section>
