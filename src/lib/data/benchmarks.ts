export type BenchmarkRow = { method: string; values: string[] };
export type Benchmark = {
  label: string;
  heading: string;
  description: string;
  metrics: { label: string; direction: string }[];
  groups: { label: string; rows: BenchmarkRow[] }[];
  notes: string[];
};
// Values transcribed directly from Table I in ral-letter/main.tex.
export const benchmarks: Benchmark[] = [
  {
    label: "Future contact-point estimation on EgoContact",
    heading: "Future contact-point estimation.",
    description:
      "Object localization and contact precision across 22,523 EgoContact events.",
    metrics: [
      {
        label: "PiB",
        direction: "↑",
      },
      {
        label: "mDST",
        direction: "↓",
      },
      {
        label: "PCK@1%",
        direction: "↑",
      },
      {
        label: "PCK@5%",
        direction: "↑",
      },
    ],
    groups: [
      {
        label: "Naive baseline",
        rows: [
          {
            method: "BBox center",
            values: [
              "100.0",
              "100.0",
              "0.04",
              "0.04",
              "7.36",
              "7.36",
              "73.78",
              "73.78",
            ],
          },
        ],
      },
      {
        label: "Affordance grounding",
        rows: [
          {
            method: "GLOVER++",
            values: [
              "21.02",
              "28.32",
              "0.16",
              "0.14",
              "0.92",
              "2.79",
              "14.43",
              "20.59",
            ],
          },
          {
            method: "3DOI",
            values: [
              "59.96",
              "75.33",
              "0.10",
              "0.06",
              "3.49",
              "11.95",
              "39.30",
              "60.62",
            ],
          },
        ],
      },
      {
        label: "Affordance transfer",
        rows: [
          {
            method: "RAM",
            values: [
              "29.49",
              "40.41",
              "0.17",
              "0.13",
              "1.47",
              "4.63",
              "17.95",
              "31.22",
            ],
          },
          {
            method: "Robo-ABC",
            values: ["33.69", "—", "0.19", "—", "1.59", "—", "18.02", "—"],
          },
        ],
      },
      {
        label: "VLMs",
        rows: [
          {
            method: "RoboPoint",
            values: [
              "42.18",
              "50.25",
              "0.13",
              "0.11",
              "1.19",
              "5.04",
              "26.47",
              "40.78",
            ],
          },
          {
            method: "MolmoPoint",
            values: [
              "45.70",
              "49.66",
              "0.14",
              "0.12",
              "2.55",
              "3.09",
              "31.94",
              "35.91",
            ],
          },
          {
            method: "Qwen 3.8 27B",
            values: [
              "13.74",
              "22.56",
              "0.25",
              "0.21",
              "0.34",
              "1.73",
              "7.78",
              "16.30",
            ],
          },
          {
            method: "Gemma 4 31B",
            values: [
              "13.68",
              "20.71",
              "0.22",
              "0.19",
              "0.45",
              "1.25",
              "8.27",
              "14.54",
            ],
          },
          {
            method: "Muse Spark 1.3",
            values: [
              "57.32",
              "79.91",
              "0.10",
              "0.05",
              "3.44",
              "11.05",
              "42.35",
              "71.82",
            ],
          },
        ],
      },
    ],
    notes: [
      "PiB and PCK are percentages; mDST is normalized distance. See the paper for metric definitions and evaluation details.",
    ],
  },
];
export const lastUpdated = "23/10/2026";
