<script lang="ts">
  import TextBlock from "#lib/components/TextBlock.svelte";
  import SectionHeading from "#lib/components/SectionHeading.svelte";
  import ColumnChart from "#lib/components/ColumnChart.svelte";
  import {
    graspSeries,
    simulationGrasps,
    realRobotGrasps,
  } from "#lib/data/grasp-results.js";
</script>

<section
  id="robotic-manipulation"
  class="mb-6 mt-6"
  aria-label="Research question 2"
  tabindex="-1"
>
  <SectionHeading title="RQ2: How does it translate to robotic manipulation?" />
  <TextBlock>
    <p>
      Does the contact understanding measured by EgoContact help a robot
      manipulate objects? We test this with RAM, a policy that transfers
      contacts from past interactions, by replacing its original memory bank
      with EgoContact and evaluating grasp success in simulation and on a real
      robot.
    </p>
  </TextBlock>

  <section id="grasp-setup" aria-labelledby="grasp-setup-heading" tabindex="-1">
    <h3 id="grasp-setup-heading" class="subsection-heading">
      Experimental setup
    </h3>
    <TextBlock>
      <p>
        Given an object image and an action query, RAM retrieves a reference
        interaction and transfers its contact to the target object. This contact
        guides selection among grasp proposals. <strong
          >Only the memory bank changes; the policy stays fixed, with no
          fine-tuning.</strong
        >
      </p>
    </TextBlock>
    <figure class="experiment-figure">
      <img
        src="/images/grasp-pipeline.webp"
        width="2400"
        height="650"
        loading="lazy"
        alt="Grasp evaluation pipeline: an object observation and action query guide retrieval from a memory bank; a transferred contact guides grasp selection, then evaluation in simulation and on a real robot."
      />
      <figcaption class="figure-caption">
        The same retrieval, contact-transfer, and grasp-selection procedure is
        used with each memory bank.
      </figcaption>
    </figure>
  </section>

  <div id="grasp-results" class="experiment-results">
    <section
      id="simulation"
      class="experiment-result"
      aria-label="Evaluation in simulation"
      tabindex="-1"
    >
      <h3 class="subsection-heading">Simulation Results</h3>
      <TextBlock>
        <p>
          We use the object set curated by <a
            href="https://irvlutd.github.io/MultiGripperGrasp/"
            >MultiGripperGrasp</a
          >: 346 objects from GSO and YCB, evaluated in Isaac Sim with one grasp
          per object. RAM receives an object observation and the instruction
          “pick up.” Its predicted contact is projected into the object point
          cloud to select the nearest
          <a href="https://graspgenx.github.io/">GraspGenX</a> proposal. A grasp succeeds
          if the object remains held under gravity for at least three seconds.
        </p>
      </TextBlock>
      <figure class="experiment-figure">
        <ColumnChart
          label="Simulation grasp success"
          axisLabel="Success rate (%)"
          groups={simulationGrasps}
          series={graspSeries}
          maximum={40}
          tickStep={10}
          decimals={1}
          suffix="%"
        />
      </figure>
    </section>
    <section
      id="real-robot"
      class="experiment-result"
      aria-label="Evaluation on a real robot"
      tabindex="-1"
    >
      <h3 class="subsection-heading">Real Robot Results</h3>
      <TextBlock>
        <p>
          We use a Franka Panda arm with an RGB-D camera and AnyGrasp proposals,
          following the same contact-transfer and grasp-selection procedure.
          Each memory bank is tested on five objects, with ten trials per
          object. The robot closes its gripper and lifts the object; a trial
          succeeds if the object remains held after lifting.
        </p>
      </TextBlock>
      <figure class="experiment-figure">
        <ColumnChart
          label="Real-robot grasp success"
          axisLabel="Successful grasps (out of 10)"
          groups={realRobotGrasps}
          series={graspSeries}
          maximum={10}
          tickStep={2}
        />
      </figure>
    </section>
  </div>
  <TextBlock>
    <p>
      <strong
        >EgoContact improves grasp selection without further training.</strong
      >
      This comparison measures the benefit of the memory bank as a whole, including
      both its interaction coverage and contact annotations.
    </p>
  </TextBlock>
</section>

<style>
  .subsection-heading {
    font-size: 1.15rem;
    font-weight: 600;
    color: #111;
    margin: 2rem 0 1rem;
  }
  .experiment-results {
    margin-bottom: 2rem;
  }
  .experiment-result + .experiment-result {
    padding-top: 0.5rem;
  }
  .experiment-result {
    min-width: 0;
    width: 100%;
  }
  .experiment-result .experiment-figure {
    max-width: 640px;
    margin: 0 auto;
  }
  .experiment-figure {
    margin: 0;
  }
  .experiment-figure img {
    display: block;
    width: 100%;
    height: auto;
  }
</style>
