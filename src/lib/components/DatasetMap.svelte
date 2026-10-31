<script lang="ts">
  import * as d3 from "d3";
  import VideoDialog from "#lib/components/VideoDialog.svelte";
  type MapNode = {
    id: string;
    label: string;
    x: number;
    y: number;
    r: number;
    cluster: number;
    video?: string;
  };
  let selected = $state<MapNode | null>(null);
  let error = $state("");
  function renderMap(container: HTMLDivElement) {
    const controller = new AbortController();
    const tooltip = d3
      .select(container)
      .append("div")
      .style("position", "fixed")
      .style("z-index", "20")
      .style("background", "rgba(15,23,42,.9)")
      .style("color", "white")
      .style("padding", "5px 10px")
      .style("border-radius", "6px")
      .style("font-size", "12px")
      .style("pointer-events", "none")
      .style("opacity", "0");
    let observer: ResizeObserver | undefined;
    let svg: d3.Selection<SVGSVGElement, unknown, null, undefined> | undefined;
    fetch("/data/tsne.json", { signal: controller.signal })
      .then((response) => {
        if (!response.ok) throw new Error("Dataset map could not be loaded.");
        return response.json();
      })
      .then((data: MapNode[]) => {
        if (controller.signal.aborted) return;
        const draw = () => {
          svg?.remove();
          const width = container.clientWidth,
            height = container.clientHeight;
          if (!width || !height) return;
          svg = d3
            .select(container)
            .append("svg")
            .attr("width", width)
            .attr("height", height)
            .attr(
              "aria-label",
              "Interactive dataset map: pan, zoom, or select an interaction",
            )
            .style("cursor", "move");
          const group = svg.append("g");
          svg.call(
            d3
              .zoom<SVGSVGElement, unknown>()
              .scaleExtent([0.5, 5])
              .on("zoom", (event) => group.attr("transform", event.transform)),
          );
          const color = d3
            .scaleSequential(d3.interpolateViridis)
            .domain(d3.extent(data, (d) => d.x) as [number, number]);
          const x = d3
            .scaleLinear()
            .domain([0, 100])
            .range([50, width - 50]);
          const y = d3
            .scaleLinear()
            .domain([0, 100])
            .range([50, height - 50]);
          const move = (event: MouseEvent) =>
            tooltip
              .style("left", `${event.clientX + 10}px`)
              .style("top", `${event.clientY - 20}px`);
          group
            .selectAll("circle")
            .data(data)
            .join("circle")
            .attr("cx", (d) => x(d.x))
            .attr("cy", (d) => y(d.y))
            .attr("r", (d) => d.r)
            .attr("fill", (d) => color(d.x))
            .attr("stroke", (d) => d3.color(color(d.x))!.darker(0.9).toString())
            .attr("stroke-width", (d) => (d.video ? 1.6 : 0.8))
            .style("opacity", 0.72)
            .style("cursor", (d) => (d.video ? "pointer" : "default"))
            .attr("tabindex", (d) => (d.video ? 0 : null))
            .attr("role", (d) => (d.video ? "button" : null))
            .attr("aria-label", (d) =>
              d.video ? `Play interaction: ${d.label}` : d.label,
            )
            .on("mouseover", function (event: MouseEvent, d) {
              d3.select(this)
                .attr("r", d.r * 1.5)
                .style("opacity", 1);
              tooltip.text(d.label).style("opacity", 1);
              move(event);
            })
            .on("mousemove", move)
            .on("mouseout", function (_event, d) {
              d3.select(this).attr("r", d.r).style("opacity", 0.8);
              tooltip.style("opacity", 0);
            })
            .on("click", (_event, d) => {
              if (d.video) {
                tooltip.style("opacity", 0);
                selected = d;
              }
            })
            .on("keydown", (event: KeyboardEvent, d) => {
              if (d.video && (event.key === "Enter" || event.key === " ")) {
                event.preventDefault();
                selected = d;
              }
            });
          const representatives = Array.from(
            d3.group(data, (d) => d.cluster).values(),
            (nodes) =>
              nodes.reduce((best, node) =>
                node.r > best.r ||
                (node.r === best.r && node.video && !best.video)
                  ? node
                  : best,
              ),
          );
          const labels = group
            .selectAll(".cluster-label")
            .data(representatives)
            .join("g")
            .attr("class", "cluster-label")
            .attr(
              "transform",
              (d) => `translate(${x(d.x)},${y(d.y) - d.r - 8})`,
            )
            .style("pointer-events", "none");
          labels
            .append("text")
            .attr("text-anchor", "middle")
            .attr("dominant-baseline", "middle")
            .text((d) => d.label)
            .style("font-size", "11px")
            .style("font-weight", "700")
            .style("fill", "#374151");
          labels.each(function () {
            const g = d3.select(this),
              box = g.select<SVGTextElement>("text").node()!.getBBox();
            g.insert("rect", "text")
              .attr("x", box.x - 6)
              .attr("y", box.y - 3)
              .attr("width", box.width + 12)
              .attr("height", box.height + 6)
              .attr("rx", 4)
              .attr("fill", "rgba(255,255,255,.82)")
              .attr("stroke", "rgba(107,114,128,.72)")
              .attr("stroke-width", 1.1);
          });
        };
        observer = new ResizeObserver(draw);
        observer.observe(container);
      })
      .catch((reason: Error) => {
        if (reason.name !== "AbortError") error = reason.message;
      });
    return {
      destroy() {
        controller.abort();
        observer?.disconnect();
        svg?.remove();
        tooltip.remove();
      },
    };
  }
</script>

<div id="content-realworld" class="dataset-content-block">
  <h3 class="title is-4 has-text-centered mb-4">Interactive Dataset Map</h3>
  <div class="content has-text-centered mb-4">
    <p>
      Explore the diverse distribution of interactions in EgoContact. This
      data-driven t-SNE visualization is fully interactive. <br /><strong
        >Pan, zoom, and click the larger bubbles to watch the exact 2.5-second
        interaction clip!</strong
      >
    </p>
  </div>
  <div
    class="box p-0"
    style="overflow: hidden; border: 1px solid #e2e8f0; border-radius: 12px; box-shadow: 0 10px 25px rgba(0,0,0,0.05); text-align: center;"
  >
    <div
      id="tsne-container"
      use:renderMap
      style="width: 100%; height: 600px; background-color: #f8fafc; position: relative;"
    ></div>
  </div>
</div>

{#if error}<p role="alert">{error}</p>{/if}
{#if selected?.video}
  <VideoDialog
    label={selected.label}
    src={selected.video}
    onclose={() => (selected = null)}
  />
{/if}
