<script>
    import Popover from "./Popover.svelte";

    export let open = false;
    export let label = "";
    export let triggerContent = "";
    export let panelContent = '';
</script>

<Popover open={open} label={label}>
    <p slot="trigger">{triggerContent}</p>
    <p slot="panel">{panelContent}</p>
</Popover>