<script lang="ts">
  import TextBlock from "#lib/components/TextBlock.svelte";
  import SectionHeading from "#lib/components/SectionHeading.svelte";
</script>

<figure class="project-teaser">
  <img
    src="/images/egocontact-teaser.webp"
    width="2600"
    height="851"
    alt="EgoContact overview: diverse everyday interactions, two annotated contacts transferred from a contact frame to a pre-contact observation, and a robot reasoning about where to grasp a cup."
    fetchpriority="high"
  />
  <figcaption class="figure-caption">
    <strong>Overview of EgoContact.</strong> Egocentric video offers a scalable
    source of interactions with the environment. We use the captured human
    behavior to probe what the environment affords. Across diverse interactions
    (<strong>left</strong>), we annotate objects, actions, and contact points in
    contact and pre-contact frames (<strong>middle</strong>), enabling
    evaluation of where models predict contact for an intended action (<strong
      >right</strong
    >).
  </figcaption>
</figure>
<section
  id="abstract"
  class="abstract-section columns is-centered"
  aria-label="Abstract"
  tabindex="-1"
>
  <div class="column is-four-fifths">
    <SectionHeading title="Abstract" />
    <TextBlock abstract>
      <p>
        Egocentric video has emerged as one of the most scalable sources of data
        for learning generalizable manipulation priors. Yet, despite its growing
        use in pretraining robotic policies, it has been underutilized as a
        validation tool for physical intelligence, a key component of which is
        understanding where to make contact with an object to achieve an
        intended interaction. We present <strong>EgoContact</strong>, a
        large-scale egocentric dataset for evaluating the generalizability and
        precision of learned manipulation priors through
        <em>future contact-point prediction</em>. EgoContact contains 22.5K
        manually verified interaction events, each with a pre-contact
        observation, semantic intent, and pixel-precise contact locations. We
        find that current methods often struggle to predict precise interaction
        contacts and sometimes fail to localize the target object in diverse,
        in-the-wild scenes, even when allowed multiple predictions. Furthermore,
        we demonstrate the usefulness of EgoContact's annotated interactions for
        robotic manipulation: simply using EgoContact as the memory bank of an
        existing affordance-transfer policy improves grasp success from 14.2% to
        31.2% in simulation and from 16% to 58% on a real robot.
      </p>
    </TextBlock>
  </div>
</section>
