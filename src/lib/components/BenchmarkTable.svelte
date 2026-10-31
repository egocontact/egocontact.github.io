<script lang="ts">
  import type { Benchmark } from "#lib/data/benchmarks.js";
  let { benchmark }: { benchmark: Benchmark } = $props();
</script>

<div class="content">
  <p><strong>{benchmark.heading}</strong> {benchmark.description}</p>
</div>
<!-- svelte-ignore a11y_no_noninteractive_tabindex (The results region is focusable so keyboard users can scroll the table.) -->
<div
  class="table-scroll"
  role="region"
  aria-label="Contact prediction results"
  tabindex="0"
>
  <table
    class="table is-fullwidth is-hoverable leaderboard-table"
    aria-label={benchmark.label}
    aria-describedby="benchmark-notes"
  >
    <colgroup><col /></colgroup>
    {#each benchmark.metrics as metric}<colgroup span="2"></colgroup>{/each}
    <thead>
      <tr>
        <th scope="col" rowspan="2">Method</th>
        {#each benchmark.metrics as metric}
          <th scope="colgroup" colspan="2">
            <span class="metric-label"
              >{metric.label}<span class="metric-direction">
                {metric.direction}</span
              ></span
            >
          </th>
        {/each}
      </tr>
      <tr>
        {#each benchmark.metrics as metric}
          <th scope="col">Top-1</th><th scope="col">Top-5</th>
        {/each}
      </tr>
    </thead>
    {#each benchmark.groups as group}
      <tbody>
        <tr class="benchmark-group">
          <th scope="rowgroup" colspan={1 + benchmark.metrics.length * 2}
            >{group.label}</th
          >
        </tr>
        {#each group.rows as row}
          <tr>
            <th scope="row">{row.method}</th>
            {#each row.values as value}<td>{value}</td>{/each}
          </tr>
        {/each}
      </tbody>
    {/each}
  </table>
</div>
<div class="content benchmark-notes" id="benchmark-notes">
  <p>{benchmark.notes.join(" ")}</p>
</div>
