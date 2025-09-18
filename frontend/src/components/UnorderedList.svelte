<script lang="ts">
    let { children } = $props();;
</script>

 <ul class="list-disc pl-6 mb-6 text-neutral-700 space-y-2 [&>li]:text-lg">{@render children()}</ul>