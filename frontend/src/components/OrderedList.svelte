<script lang="ts">
    let { children } = $props();;
</script>

 <ol class="list-decimal pl-6 mb-8 text-neutral-700 space-y-2 [&>li]:text-lg">{@render children()}</ol>