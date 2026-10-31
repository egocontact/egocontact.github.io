import { assert } from "#lib/utils/assert.js";

export type ChartSeries = { key: string; label: string; color: string };
export type ChartGroup = {
  label: string;
  detail?: string;
  image?: string;
  values: Record<string, number>;
};

export function assertChartData(
  groups: ChartGroup[],
  series: ChartSeries[],
  maximum: number,
  tickStep: number,
  decimals: number,
) {
  assert(
    Number.isFinite(maximum) && maximum > 0,
    "Chart maximum must be positive.",
  );
  assert(
    Number.isFinite(tickStep) && tickStep > 0 && tickStep <= maximum,
    "Chart tick step must be positive and no larger than the maximum.",
  );
  assert(
    Number.isInteger(decimals) && decimals >= 0 && decimals <= 100,
    "Chart decimals must be an integer between 0 and 100.",
  );
  assert(
    groups.length > 0 && series.length > 0,
    "Chart needs groups and series.",
  );
  assert(
    new Set(series.map((item) => item.key)).size === series.length,
    "Chart series keys must be unique.",
  );
  for (const group of groups) {
    for (const item of series) {
      const value = group.values[item.key];
      assert(
        Number.isFinite(value) && value >= 0 && value <= maximum,
        `Invalid chart value for ${group.label}/${item.key}: ${value} (maximum ${maximum}).`,
      );
    }
  }
}
