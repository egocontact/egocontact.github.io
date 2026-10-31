/** Throw in production too: invalid authored data must fail the build/render. */
export function assert(condition: unknown, message: string): asserts condition {
  if (!condition) throw new Error(message);
}
