<script lang="ts">
  import { onMount } from "svelte";
  import { title, affiliations } from "#lib/data/project.js";

  import { sections } from "#lib/data/navigation.js";
  import { trackSections } from "#lib/utils/track-sections.js";
  const targetIds = sections.map((section) => section.id);
  // Follow the affiliation order in ral-letter/main.tex.
  const affiliationLogos = [
    { id: 1, file: "cambridge.svg", url: "https://www.cam.ac.uk/" },
    { id: 2, file: "tum.svg", url: "https://www.tum.de/en/" },
    { id: 3, file: "eth.png", url: "https://ethz.ch/en.html" },
    { id: 5, file: "microsoft.png", url: "https://www.microsoft.com/" },
    { id: 6, file: "ulm.png", url: "https://www.uni-ulm.de/en/" },
    { id: 4, file: "mcml.svg", url: "https://mcml.ai/" },
  ].map((logo) => ({
    ...logo,
    name: affiliations.find((affiliation) => affiliation.id === logo.id)!.name,
  }));
  let open = $state(false);
  let active = $state("overview");
  let sidebar: HTMLElement;
  let menuButton: HTMLButtonElement;

  onMount(() => {
    const stopTracking = trackSections(targetIds, (id) => {
      active = id;
    });
    const escape = (event: KeyboardEvent) => {
      if (event.key === "Escape" && open) {
        open = false;
        menuButton.focus();
      }
    };
    const outside = (event: PointerEvent) => {
      if (open && !sidebar.contains(event.target as Node)) open = false;
    };
    document.addEventListener("keydown", escape);
    document.addEventListener("pointerdown", outside);
    return () => {
      stopTracking();
      document.removeEventListener("keydown", escape);
      document.removeEventListener("pointerdown", outside);
    };
  });
</script>

<a class="skip-to-content" href="#main-content">Skip to content</a>
<aside
  class="reading-sidebar"
  aria-label="Paper navigation"
  bind:this={sidebar}
>
  <div class="mobile-bar">
    <a href="#overview" class="mobile-brand" onclick={() => (open = false)}
      >EgoContact</a
    >
    <button
      type="button"
      bind:this={menuButton}
      aria-expanded={open}
      aria-controls="paper-navigation"
      onclick={() => (open = !open)}
    >
      Contents <span class:turned={open} aria-hidden="true">⌄</span>
    </button>
  </div>
  <div id="paper-navigation" class="nav-panel" class:expanded={open}>
    <header class="paper-identity">
      <a
        href="#overview"
        class="paper-name"
        aria-label={title}
        onclick={() => (open = false)}>EgoContact</a
      >
      <p>{title.replace("EgoContact: ", "")}</p>
    </header>
    <nav aria-label="On this page">
      <p class="contents-label">Contents</p>
      <ol class="contents-list">
        {#each sections as section, index}
          <li>
            <a
              href={`#${section.id}`}
              class:current={active === section.id}
              aria-current={active === section.id ? "location" : undefined}
              onclick={() => (open = false)}
            >
              <span class="section-number" aria-hidden="true"
                >{String(index + 1).padStart(2, "0")}</span
              >
              <span class="section-label">
                {#if section.tag}<em>{section.tag}:</em>&nbsp;{/if}{section.label}
              </span>
            </a>
          </li>
        {/each}
      </ol>
    </nav>
    <footer class="affiliation-footer" aria-label="Affiliations">
      <ul class="affiliation-logos">
        {#each affiliationLogos as logo}
          <li>
            <a href={logo.url} aria-label={logo.name} title={logo.name}>
              <span
                class="affiliation-logo"
                class:ulm={logo.id === 6}
                class:tum={logo.id === 2}
                style={`--logo: url('/images/affiliations/${logo.file}')`}
              ></span>
            </a>
          </li>
        {/each}
      </ul>
    </footer>
  </div>
</aside>

<style>
  .skip-to-content {
    position: fixed;
    top: 12px;
    left: 16px;
    z-index: 100;
    transform: translateY(-180%);
    padding: 10px 16px;
    background: white;
    color: #111;
    border: 2px solid #111;
  }
  .skip-to-content:focus {
    transform: translateY(0);
  }
  .reading-sidebar {
    position: fixed;
    inset: 0 auto 0 0;
    width: var(--reading-sidebar-width);
    z-index: 40;
    background: #111;
    color: white;
  }
  .nav-panel {
    display: flex;
    flex-direction: column;
    height: 100%;
    overflow-y: auto;
    padding: 42px 24px 24px;
    scrollbar-width: thin;
    scrollbar-color: #555 #111;
  }
  .nav-panel > nav,
  .paper-identity,
  .affiliation-footer {
    flex-shrink: 0;
  }
  .affiliation-footer {
    margin-top: auto;
    padding-top: 32px;
  }
  .affiliation-logos {
    display: grid;
    grid-template-columns: repeat(3, minmax(0, 1fr));
    align-items: center;
    gap: 14px 18px;
    list-style: none;
    border-top: 1px solid #444;
    margin: 0;
    padding: 18px 0 0;
  }
  .affiliation-logos a {
    display: flex;
    align-items: center;
    justify-content: center;
    min-height: 30px;
  }
  .affiliation-logo {
    display: block;
    width: 100%;
    height: 20px;
    background: #fff;
    mask: var(--logo) center / contain no-repeat;
    -webkit-mask: var(--logo) center / contain no-repeat;
  }
  .affiliation-logo.tum {
    width: 38px;
  }
  .affiliation-logo.ulm {
    height: 30px;
  }
  .paper-name,
  .mobile-brand {
    color: #fff;
    font-family: var(--font-body);
    font-size: 2rem;
    font-weight: 600;
    line-height: 1.1;
    letter-spacing: -0.035em;
  }
  .paper-identity {
    border-bottom: 1px solid #444;
    padding-bottom: 30px;
    margin-bottom: 28px;
  }
  .paper-identity p {
    color: #c7c7c7;
    font-size: 0.84rem;
    line-height: 1.65;
    margin-top: 14px;
    max-width: 210px;
  }
  .contents-label {
    color: #a0a0a0;
    font-size: 0.62rem;
    text-transform: uppercase;
    letter-spacing: 0.16em;
    margin: 0 0 14px;
  }
  .contents-list {
    list-style: none;
    padding: 0;
    margin: 0;
  }
  .contents-list > li {
    margin-bottom: 16px;
  }
  .contents-list > li > a {
    display: grid;
    grid-template-columns: 20px minmax(0, 1fr);
    align-items: baseline;
    gap: 10px;
    padding: 9px 8px;
    margin: 0 -8px;
    color: #c9c9c9;
    line-height: 1.5;
  }
  .section-number {
    font-size: 0.62rem;
    color: #a0a0a0;
    font-variant-numeric: tabular-nums;
  }
  .section-label {
    font-size: 0.875rem;
    font-weight: 600;
  }
  .contents-list a:hover {
    color: white;
  }
  .contents-list > li > a.current {
    color: #111;
    background: #fff;
  }
  .contents-list > li > a.current .section-number {
    color: #444;
  }
  a:focus-visible,
  button:focus-visible {
    outline: 2px solid white;
    outline-offset: 4px;
  }
  .mobile-bar {
    display: none;
  }
  @media (max-width: 1099px) {
    .reading-sidebar {
      position: sticky;
      inset: auto;
      top: 0;
      width: 100%;
    }
    .mobile-bar {
      display: flex;
      height: 64px;
      padding: 0 24px;
      align-items: center;
      justify-content: space-between;
      border-bottom: 1px solid #444;
    }
    .mobile-brand {
      font-size: 1.4rem;
      letter-spacing: -0.035em;
    }
    .mobile-bar button {
      display: flex;
      align-items: center;
      gap: 12px;
      border: 1px solid #777;
      border-radius: 0;
      background: transparent;
      color: white;
      font: inherit;
      font-size: 0.75rem;
      padding: 6px 12px;
      cursor: pointer;
    }
    .mobile-bar button span {
      font-size: 1rem;
    }
    .mobile-bar button span.turned {
      transform: rotate(180deg);
    }
    .nav-panel {
      display: none;
      position: absolute;
      top: 64px;
      left: 0;
      right: 0;
      height: auto;
      max-height: calc(100dvh - 64px);
      padding: 24px;
      background: #111;
      border-bottom: 1px solid #444;
    }
    .nav-panel.expanded {
      display: block;
    }
    .paper-identity {
      display: none;
    }
    .contents-list > li {
      margin-bottom: 12px;
    }
    .contents-list > li > a {
      min-height: 36px;
    }
    .section-label {
      font-size: 0.86rem;
    }
  }
  @media print {
    .reading-sidebar,
    .skip-to-content {
      display: none;
    }
  }
</style>
