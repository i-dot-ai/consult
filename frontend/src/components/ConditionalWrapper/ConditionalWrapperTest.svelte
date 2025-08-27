<script lang="ts">
    import ConditionalWrapper from "./ConditionalWrapper.svelte";

    export let element = false;
    export let condition: boolean = false;
    export let slot: string = "";
</script>

<ConditionalWrapper element={element} condition={condition}>
    {@html slot}
</ConditionalWrapper>