<script lang="ts">
  import {
    assertChartData,
    type ChartSeries,
    type ChartGroup,
  } from "./column-chart.js";
  let {
    label,
    axisLabel,
    groups,
    series,
    maximum,
    tickStep,
    decimals = 0,
    suffix = "",
  }: {
    label: string;
    axisLabel: string;
    groups: ChartGroup[];
    series: ChartSeries[];
    maximum: number;
    tickStep: number;
    decimals?: number;
    suffix?: string;
  } = $props();
  const ticks = $derived.by(() => {
    assertChartData(groups, series, maximum, tickStep, decimals);
    return Array.from(
      { length: Math.floor(maximum / tickStep) + 1 },
      (_, i) => i * tickStep,
    );
  });
  const hasImages = $derived(groups.some((group) => group.image));
  const format = (value: number) => `${value.toFixed(decimals)}${suffix}`;
</script>

<div class="column-chart" aria-label={label}>
  <!-- svelte-ignore a11y_no_noninteractive_tabindex (Keyboard users need to focus and scroll the chart on narrow screens.) -->
  <div
    class="chart-scroll"
    role="region"
    aria-label={`${label}: column chart`}
    tabindex="0"
  >
    <div
      class="chart-layout"
      style={`--groups: ${groups.length}; --series: ${series.length}`}
    >
      <div class="plot">
        <p class="axis-label">{axisLabel}</p>
        <div class="grid" aria-hidden="true">
          {#each ticks as tick}<div
              class="grid-line"
              style:bottom={`${(tick / maximum) * 100}%`}
            >
              <span>{tick}</span>
            </div>{/each}
        </div>
        <div class="column-groups">
          {#each groups as group}
            <div class="column-group" role="group" aria-label={group.label}>
              {#each series as item}
                <div
                  class="column"
                  style:height={`${(group.values[item.key] / maximum) * 100}%`}
                >
                  <span class="value"
                    ><span class="visually-hidden">{item.label}: </span>{format(
                      group.values[item.key],
                    )}</span
                  >
                  <span
                    class="bar"
                    style:background={item.color}
                    aria-hidden="true"
                  ></span>
                </div>
              {/each}
            </div>
          {/each}
        </div>
      </div>
      <div class="category-labels">
        {#each groups as group}
          <div class="category">
            {#if hasImages}<div class="object-image">
                {#if group.image}<img
                    src={group.image}
                    alt=""
                    loading="lazy"
                  />{/if}
              </div>{/if}
            <span>{group.label}</span>
            {#if group.detail}<small>{group.detail}</small>{/if}
          </div>
        {/each}
      </div>
    </div>
  </div>
  <div class="chart-legend" aria-label="Chart legend">
    {#each series as item}<span
        ><i style:background={item.color} aria-hidden="true"
        ></i>{item.label}</span
      >{/each}
  </div>
</div>

<style>
  .column-chart {
    color: #111;
    margin: 1.5rem auto 0;
  }
  .axis-label {
    position: absolute;
    left: -66px;
    top: 0;
    height: 100%;
    margin: 0;
    font-size: 0.8rem;
    text-align: center;
    white-space: nowrap;
    writing-mode: vertical-rl;
    transform: rotate(180deg);
  }
  .chart-scroll {
    overflow-x: auto;
    padding: 24px 0 8px;
  }
  .chart-scroll:focus-visible {
    outline: 2px solid #111;
    outline-offset: 4px;
  }
  .chart-layout {
    min-width: calc(
      var(--groups) * max(86px, calc(var(--series) * 36px + 14px)) + 72px
    );
    padding-left: 72px;
    padding-right: 4px;
  }
  .plot {
    height: 240px;
    position: relative;
    border-left: 1px solid #999;
    border-bottom: 1px solid #555;
  }
  .grid {
    position: absolute;
    inset: 0;
    pointer-events: none;
  }
  .grid-line {
    position: absolute;
    left: 0;
    right: 0;
    border-top: 1px solid #e6e6e6;
  }
  .grid-line:first-child {
    border-top: 0;
  }
  .grid-line > span {
    position: absolute;
    right: calc(100% + 10px);
    transform: translateY(-50%);
    color: #666;
    font-size: 0.75rem;
    font-variant-numeric: tabular-nums;
  }
  .column-groups {
    position: absolute;
    inset: 0;
    display: grid;
    grid-template-columns: repeat(var(--groups), minmax(0, 1fr));
  }
  .column-group {
    display: flex;
    align-items: end;
    justify-content: center;
    gap: 7px;
    padding: 0 10px;
  }
  .column {
    position: relative;
    flex: 1;
    max-width: 42px;
    min-width: 0;
    padding: 0;
  }
  .bar {
    position: absolute;
    inset: 0;
  }
  .value {
    position: absolute;
    bottom: calc(100% + 7px);
    left: 50%;
    transform: translateX(-50%);
    font-size: 0.8rem;
    line-height: 1;
    white-space: nowrap;
    font-variant-numeric: tabular-nums;
  }
  .category-labels {
    display: grid;
    grid-template-columns: repeat(var(--groups), minmax(0, 1fr));
    margin-top: 12px;
  }
  .category {
    text-align: center;
    font-size: 0.8rem;
    line-height: 1.4;
  }
  .category small {
    display: block;
    margin-top: 3px;
    color: #666;
    font-size: 0.65rem;
  }
  .object-image {
    height: 62px;
    margin: 0 10px 8px;
  }
  .object-image img {
    display: block;
    width: 100%;
    height: 100%;
    object-fit: contain;
  }
  .chart-legend {
    display: flex;
    flex-wrap: wrap;
    justify-content: center;
    gap: 24px;
    margin: 18px 0 0;
    font-size: 0.8rem;
  }
  .chart-legend > span {
    display: inline-flex;
    align-items: center;
    gap: 8px;
  }
  .chart-legend i {
    width: 22px;
    height: 10px;
  }
  .visually-hidden {
    position: absolute;
    width: 1px;
    height: 1px;
    padding: 0;
    margin: -1px;
    overflow: hidden;
    clip-path: inset(50%);
    white-space: nowrap;
  }
  @media (max-width: 600px) {
    .plot {
      height: 210px;
    }
    .column-group {
      gap: 6px;
      padding: 0 12px;
    }
    .value {
      font-size: 0.72rem;
    }
  }
</style>
