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
    } from 'chart.js';


    interface Props {
        data: number[];
        labels: string[];
    }

    let {
        data = [],
        labels = [],
    }: Props = $props();

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

        let listContainer = legendContainer.querySelector('ul');

        if (!listContainer) {
            listContainer = document.createElement('ul');
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
        id: 'htmlLegend',
        afterUpdate(chart: Chart, args: any, options: ChartOptions) {
            //@ts-ignore: containerID added by plugin
            const ul = getOrCreateLegendList(chart, options.containerID);

            // Clear legend
            while (ul.firstChild) {
                ul.firstChild.remove();
            }

            // Generate legendItems with built-in generator
            const items: LegendItem[] | undefined = chart?.options?.plugins?.legend?.labels?.generateLabels?.(chart);

            if (!items) {
                throw new Error("Incorrect chart configuration");
            }

            items.forEach(item => {
                const li = document.createElement('li');
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
                    const {type} = chart.config as ChartConfiguration;
                    if (type === 'pie' || type === 'doughnut') {
                        chart.toggleDataVisibility(item.index || 0);
                    } else {
                        chart.setDatasetVisibility(item.datasetIndex || 0, !chart.isDatasetVisible(item.datasetIndex || 0));
                    }
                    chart.update();
                };

                const boxSpan: HTMLElement = document.createElement('span');
                boxSpan.style.background = item.fillStyle as string;
                boxSpan.style.borderColor = item.strokeStyle as string;
                boxSpan.style.borderWidth = item.lineWidth + 'px';

                boxSpan.className = clsx([
                    "inline-block",
                    "h-3",
                    "w-3",
                    "mr-1",
                    "shrink-0",
                    "rounded-full",
                ]);

                const textContainer = document.createElement('p');
                textContainer.style.color = item.fontColor as string;
                textContainer.className = clsx([
                    "m-0",
                    "p-0",
                    item.hidden && "line-through",
                ]);

                const text = document.createTextNode(item.text);
                textContainer.appendChild(text);

                li.appendChild(boxSpan);
                li.appendChild(textContainer);
                ul.appendChild(li);
            });
        }
    };

    onMount(() => {
        if (chartElement) {
            new Chart(chartElement, {
                type: 'doughnut',
                data: {
                    labels: labels,
                    datasets: [{
                        label: ' counts',
                        data: data,
                        borderWidth: 1
                    }]
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
                        //@ts-ignore: custom plugin adds htmlLegend
                        htmlLegend: {
                            containerID: 'legend-container',
                        }
                    },
                    layout: {
                        padding: 0
                    }
                },
                plugins: [htmlLegendPlugin]
            });
        }
    })
</script>

<div class="w-full h-full">
  <canvas class="h-full" bind:this={chartElement}></canvas>
</div>