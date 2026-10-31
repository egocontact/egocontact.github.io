import { assert } from "#lib/utils/assert.js";

export type Point = { x: number; y: number; occluded?: boolean };
export type ContactKey = "contact_thumb" | "contact_index";
export type Manifest = {
  action: string;
  width: number;
  height: number;
  fps: number;
  first: number;
  observation: number;
  contact: number;
  frames: { index: number; src: string }[];
  anchors: Record<string, { contact_thumb: Point; contact_index: Point }>;
  estimated_tracks?: {
    paths: Record<
      ContactKey,
      (Point & { frame: number; annotated: boolean })[]
    >;
  };
};

/** Assertions for our generated asset, not a general-purpose JSON parser. */
export function assertManifest(data: Manifest) {
  assert(
    data.width > 0 && data.height > 0 && data.fps > 0,
    "Spacetime dimensions and frame rate must be positive.",
  );
  assert(
    typeof data.action === "string" && data.action.length > 0,
    "Spacetime action is missing.",
  );
  assert(
    data.first === data.observation && data.observation < data.contact,
    "Spacetime must run from the last observation to contact.",
  );
  assert(
    data.frames.length >= 2 &&
      data.frames[0].index === data.observation &&
      data.frames[data.frames.length - 1].index === data.contact,
    "Spacetime frames must include both endpoints.",
  );
  for (const [i, frame] of data.frames.entries()) {
    assert(
      Number.isInteger(frame.index) &&
        typeof frame.src === "string" &&
        frame.src.length > 0 &&
        (i === 0 || frame.index > data.frames[i - 1].index),
      "Spacetime frames must have sources and increasing frame indices.",
    );
  }
  const keys = ["contact_thumb", "contact_index"] as const;
  const validPoint = (point: Point | undefined) =>
    point &&
    Number.isFinite(point.x) &&
    Number.isFinite(point.y) &&
    point.x >= 0 &&
    point.x < data.width &&
    point.y >= 0 &&
    point.y < data.height;
  for (const key of keys) {
    for (const frame of [data.observation, data.contact]) {
      assert(
        validPoint(data.anchors[frame]?.[key]),
        `Missing or invalid ${key} anchor at ${frame}.`,
      );
    }
    if (data.estimated_tracks) {
      const path = data.estimated_tracks.paths[key];
      assert(
        path?.length === data.frames.length &&
          path.every(
            (point, i) =>
              point.frame === data.frames[i].index && validPoint(point),
          ),
        `Invalid spacetime track: ${key}.`,
      );
    }
  }
}
