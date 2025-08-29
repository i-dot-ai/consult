<script>
    import Panel from "./Panel.svelte";

    let {
        slot = "",
        bg = false,
        border = false,
        level = 1,
    } = $props();
</script>

<Panel {bg} {border} {level}>
    {@html slot}
</Panel>