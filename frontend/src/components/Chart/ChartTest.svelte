<script lang="ts">
    import type { Props } from "./Chart.svelte";
    import Chart from "./Chart.svelte";

    let {
        data = [],
        labels = [],
        legendId = "legend-container",
        interactive = true,
    }: Props = $props();
</script>

<div class="flex gap-4 justify-center items-center">
    <div id={legendId}></div>
    <div class="h-24">
        <Chart {data} {labels} {legendId} {interactive} />
    </div>
</div>
