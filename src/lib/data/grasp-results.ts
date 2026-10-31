import type { ChartGroup, ChartSeries } from "#lib/components/column-chart.js";

// Values from ral-letter/scripts/{simulation_grasp_figure,real_robot_grasp_figure}.py.
// Retain counts and denominators; derive percentages without rounding the data.
export const graspSeries: ChartSeries[] = [
  { key: "ram", label: "RAM", color: "#aaa" },
  { key: "egocontact", label: "EgoContact", color: "#111" },
];

export const simulationGrasps: ChartGroup[] = [
  { label: "Total", ram: 49, egocontact: 108, trials: 346 },
  { label: "GSO", ram: 46, egocontact: 104, trials: 329 },
  { label: "YCB", ram: 3, egocontact: 4, trials: 17 },
].map(({ label, ram, egocontact, trials }) => ({
  label,
  detail: `${trials} objects`,
  values: {
    ram: (100 * ram) / trials,
    egocontact: (100 * egocontact) / trials,
  },
}));

export const realRobotGrasps: ChartGroup[] = [
  { label: "Mug", ram: 2, egocontact: 5 },
  { label: "Hammer", ram: 3, egocontact: 5 },
  { label: "Pliers", ram: 3, egocontact: 6 },
  { label: "Blower", ram: 0, egocontact: 6 },
  { label: "Pan", ram: 0, egocontact: 7 },
].map(({ label, ram, egocontact }) => ({
  label,
  image: `/images/grasp-objects/${label.toLowerCase()}.webp`,
  values: { ram, egocontact },
}));
