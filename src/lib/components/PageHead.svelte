<script lang="ts">
  import { title } from "#lib/data/project.js";
  const description =
    "EgoContact evaluates physical intelligence through future contact-point prediction, with 22.5K manually verified egocentric interactions and applications to robotic grasping.";
</script>

<svelte:head>
  <title>{title}</title>
  <meta name="description" content={description} />
  <meta
    name="keywords"
    content="EgoContact, egocentric video, physical intelligence, contact prediction, robotic grasping, affordance grounding"
  />
  <meta property="og:title" content={title} />
  <meta property="og:description" content={description} />
  <meta property="og:type" content="website" />
  <meta
    property="og:image"
    content="https://egocontact.github.io/images/egocontact-teaser.webp"
  />
  <meta name="twitter:card" content="summary_large_image" />
  <link rel="stylesheet" href="/css/bulma.min.css" />
  <link
    href="https://fonts.googleapis.com/css?family=Google+Sans|Noto+Sans&display=swap"
    rel="stylesheet"
  />
  <link
    rel="stylesheet"
    href="https://cdn.jsdelivr.net/gh/jpswalsh/academicons@1/css/academicons.min.css"
  />
  <link
    rel="stylesheet"
    href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/5.15.4/css/all.min.css"
  />
</svelte:head>
