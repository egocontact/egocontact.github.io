// Original teaser event and annotations: ral-letter/assets/teaser/manifest.json,
// 8f339122-0193-4191-a0ea-d761b08ffffe_10009, frames 9994 and 10009.
// Coordinates are in the original 1440 × 1080 frames; the SVG viewBox uses
// the same crop as the paper's teaser without changing the annotations.
export const interactionExample = {
  id: "8f339122-0193-4191-a0ea-d761b08ffffe_10009",
  object: "Cup",
  verb: "Hold",
  manifestUrl: "/data/spacetime/manifest.json",
  action: "Hold the cup",
  frames: [
    {
      label: "Before contact",
      src: "/images/dataset-example-precontact.webp",
      description:
        "A cup on a table before the interaction, with its annotated target bounding box and two contact locations marked on the untouched object.",
      box: "643.68,840.24 771.12,708.48 563.76,581.04 490.32,721.44",
      thumb: { x: 556.4467005076143, y: 767.2727272727273 },
      finger: { x: 684.3654822335026, y: 647.2727272727273 },
    },
    {
      label: "At contact",
      src: "/images/dataset-example-contact.webp",
      description:
        "The hand holding the cup, with the observed thumb and opposing-finger contacts marked.",
      box: null,
      thumb: { x: 565.5837563451777, y: 818.1818181818182 },
      finger: { x: 711.7766497461929, y: 690.9090909090909 },
    },
  ],
};
