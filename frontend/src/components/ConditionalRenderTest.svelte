<script lang="ts">
    import ConditionalRender from "./ConditionalRender.svelte";

    export let element = false;
    export let condition: boolean = false;
    export let slot: string = "";
</script>

<ConditionalRender element={element} condition={condition}>
    {@html slot}
</ConditionalRender>