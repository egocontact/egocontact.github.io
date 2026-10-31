/** Track native page scrolling; returns the listener cleanup for onMount. */
export function trackSections(ids: string[], onChange: (id: string) => void) {
  const targets = ids.map((id) => ({
    id,
    element: document.getElementById(id),
  }));
  let pending = 0;
  const update = () => {
    pending = 0;
    const cutoff = window.matchMedia("(min-width: 1100px)").matches ? 96 : 132;
    let current = targets[0].id;
    let closest = -Infinity;
    const preferred = window.location.hash.slice(1);
    for (const target of targets) {
      const element = target.element;
      if (!element) continue;
      const top = element.getBoundingClientRect().top;
      // Prefer the linked target when nested sections share a top edge.
      if (
        top <= cutoff &&
        (top > closest + 1 ||
          (Math.abs(top - closest) <= 1 && target.id === preferred))
      ) {
        current = target.id;
        closest = top;
      }
    }
    if (
      window.scrollY + window.innerHeight >=
      document.documentElement.scrollHeight - 3
    )
      current = targets[targets.length - 1].id;
    onChange(current);
  };
  const schedule = () => {
    if (!pending) pending = requestAnimationFrame(update);
  };

  window.addEventListener("scroll", schedule, { passive: true });
  window.addEventListener("resize", schedule);
  window.addEventListener("hashchange", schedule);
  update();
  return () => {
    cancelAnimationFrame(pending);
    window.removeEventListener("scroll", schedule);
    window.removeEventListener("resize", schedule);
    window.removeEventListener("hashchange", schedule);
  };
}
