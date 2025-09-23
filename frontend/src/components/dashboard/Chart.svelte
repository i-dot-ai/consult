<script lang="ts">
  import clsx from "clsx";

  import { onMount } from "svelte";

  import {
    ArcElement,
    Chart,
    Colors,
    DoughnutController,
    Legend,
    Tooltip,
    registerables,
    type ChartConfiguration,
    type ChartOptions,
    type LegendItem,
  } from "chart.js";
  import { getPercentage } from "../../global/utils";

  interface LabelItem {
    text: string;
    count: number;
  }
  interface Props {
    data: number[];
    labels: LabelItem[];
    legendId?: string;
  }

  let {
    data = [],
    labels = [],
    legendId = "legend-container",
  }: Props = $props();

  const MAX_TOOLTIP_LENGTH = 20;
  const total = $derived(data.reduce((acc, curr) => acc + curr, 0));

  // Disables tree-shaking
  // Chart.register(...registerables);

  // Register required only to tree shake the rest
  Chart.register(DoughnutController, ArcElement, Legend, Colors, Tooltip);

  let chartElement: HTMLCanvasElement;

  const getOrCreateLegendList = (chart: Chart, id: string) => {
    const legendContainer = document.getElementById(id);

    if (!legendContainer) {
      throw new Error(`No legend container found with the id: ${id}`);
    }

    let listContainer = legendContainer.querySelector("ul");

    if (!listContainer) {
      listContainer = document.createElement("ul");
      listContainer.className = clsx([
        "flex",
        "flex-col",
        "m-0",
        "p-0",
        "h-full",
        "justify-around",
      ]);
      legendContainer.appendChild(listContainer);
    }

    return listContainer;
  };

  const htmlLegendPlugin = {
    id: "htmlLegend",
    afterUpdate(chart: Chart, args: any, options: ChartOptions) {
      //@ts-ignore: containerID added by plugin
      const ul = getOrCreateLegendList(chart, options.containerID);

      // Clear legend
      while (ul.firstChild) {
        ul.firstChild.remove();
      }

      // Generate legendItems with built-in generator
      const items: LegendItem[] | undefined =
        chart?.options?.plugins?.legend?.labels?.generateLabels?.(chart);

      if (!items) {
        throw new Error("Incorrect chart configuration");
      }

      items.forEach((item) => {
        const li = document.createElement("li");
        li.className = clsx([
          "flex",
          "flex-row",
          "items-center",
          "whitespace-nowrap",
          "text-ellipsis",
          "ml-2",
          "cursor-pointer",
          "text-sm",
        ]);

        li.onclick = () => {
          const { type } = chart.config as ChartConfiguration;
          if (type === "pie" || type === "doughnut") {
            chart.toggleDataVisibility(item.index || 0);
          } else {
            chart.setDatasetVisibility(
              item.datasetIndex || 0,
              !chart.isDatasetVisible(item.datasetIndex || 0),
            );
          }
          chart.update();
        };

        const boxSpan: HTMLElement = document.createElement("span");
        boxSpan.style.background = item.fillStyle as string;
        boxSpan.style.borderColor = item.strokeStyle as string;
        boxSpan.style.borderWidth = item.lineWidth + "px";

        boxSpan.className = clsx([
          "inline-block",
          "h-3",
          "w-3",
          "mr-1",
          "shrink-0",
          "rounded-full",
        ]);

        const containerEl = document.createElement("div");
        containerEl.className = clsx([
          "flex",
          "justify-between",
          "items-center",
          "w-full",
          "gap-8",
          item.hidden && "line-through",
        ]);

        const textContainer = document.createElement("p");
        textContainer.style.color = item.fontColor as string;
        textContainer.className = clsx([
          "m-0",
          "p-0",
          "max-w-[80%]",
          "whitespace-break-spaces",
          item.hidden && "line-through",
        ]);

        const text = document.createTextNode(item.text);
        textContainer.appendChild(text);

        const label = labels.find((label) => label.text === item.text);
        const count = label?.count || 0;
        const percentage = getPercentage(count, total);

        const countsContainer = document.createElement("div");
        countsContainer.className = "flex gap-2 items-center text-xs";

        const percentageEl = document.createElement("span");
        percentageEl.className = "font-bold";
        percentageEl.innerText = `${percentage}%`;

        const countsEl = document.createElement("span");
        countsEl.innerText = `(${count.toString()})`;

        countsContainer.appendChild(percentageEl);
        countsContainer.appendChild(countsEl);

        containerEl.appendChild(textContainer);
        containerEl.appendChild(countsContainer);

        li.appendChild(boxSpan);
        li.appendChild(containerEl);
        ul.appendChild(li);
      });
    },
  };

  onMount(() => {
    if (chartElement) {
      new Chart(chartElement, {
        type: "doughnut",
        data: {
          labels: labels.map((label) => label.text),
          datasets: [
            {
              label: " counts",
              data: data,
              borderWidth: 1,
            },
          ],
        },
        options: {
          responsive: true,
          maintainAspectRatio: true,
          plugins: {
            legend: {
              display: false,
              position: "right",
              align: "center",
            },
            tooltip: {
              callbacks: {
                title: (item) => {
                  const label = item.at(0)?.label || "";

                  return label?.length > MAX_TOOLTIP_LENGTH
                    ? label.slice(0, MAX_TOOLTIP_LENGTH) + "..."
                    : label;
                },
              },
            },
            //@ts-ignore: custom plugin adds htmlLegend
            htmlLegend: {
              containerID: legendId,
            },
          },
          layout: {
            padding: 0,
          },
        },
        plugins: [htmlLegendPlugin],
      });
    }
  });
</script>

<div class="w-full h-full">
  <canvas class="h-full" bind:this={chartElement}></canvas>
</div>
