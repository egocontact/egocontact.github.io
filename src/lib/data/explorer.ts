export type ExplorerSample = {
  id: string;
  object: string;
  verb: string;
  action: string;
  manifestUrl: string;
  frames: { src: string; label: string; description: string }[];
};
