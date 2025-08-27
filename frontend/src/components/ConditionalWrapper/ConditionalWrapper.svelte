<script lang="ts">
    export let element;
    export let condition;
</script>

{#if condition}
    {#if typeof element === "string"}
        <svelte:element this={element} {...$$restProps}>
            <slot />
        </svelte:element>
    {:else}
        <svelte:component this={element} {...$$restProps}>
            <slot />
        </svelte:component>
    {/if}
{:else}
    <slot />
{/if}