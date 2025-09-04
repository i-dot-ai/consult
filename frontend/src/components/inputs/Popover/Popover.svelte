<script lang="ts">
    // Using melt-ui popover
    // Docs: https://www.melt-ui.com/docs/builders/popover

    import clsx from "clsx";

    import { createPopover, createSync, melt } from '@melt-ui/svelte';
    
    import { fade } from 'svelte/transition';

    import MaterialIcon from '../../MaterialIcon.svelte';
    import KeyboardArrowDown from '../../svg/material/KeyboardArrowDown.svelte';


    export let label: string = '';
    export let open: boolean = false;
    export let arrow: boolean = true;
    export let border: boolean = true;
    export let handleOpenChange = (next: boolean) => {};

    const {
        elements: { trigger, content, close },
        states,
    } = createPopover({
        forceVisible: true,
        onOpenChange: ({ curr, next }) => {
            handleOpenChange(next);
            return next;
        }
    });

    const sync = createSync(states);
    $: sync.open(open, (value) => (open = value));
</script>


<button
    use:melt={$trigger}
    class={clsx([
        "trigger",
        "w-full",
        "p-2",
        "bg-white",
        border && clsx([
            "border",
            "border-neutral-100",
        ]),
        "rounded",
    ])}
    title={label || undefined}
    aria-label={label}
>
    <div class="flex justify-between items-center">
        <slot name="trigger" />

        {#if arrow}
            <div class={clsx([
                "transition-transform",
                "-rotate-90",
                open && "rotate-0",
            ])}>
                <MaterialIcon color="fill-neutral-400">
                    <KeyboardArrowDown />
                </MaterialIcon>
            </div>
        {/if}
    </div>
</button>

{#if open}
    <div
        use:melt={$content}
        transition:fade={{ duration: 100 }}
        class=" content bg-neutral-200"
    >
        <slot name="panel" />
    </div>
{/if}

<style lang="postcss">
    .input {
        @apply flex h-8 w-full rounded-md border border-neutral-800 bg-transparent px-2.5 text-sm;
        @apply ring-offset-neutral-300 focus-visible:ring;
        @apply focus-visible:ring-neutral-400 focus-visible:ring-offset-1;
        @apply flex-1 items-center justify-center;
        @apply px-2.5 text-sm leading-none text-neutral-700;
    }

    .trigger {
        /* @apply inline-flex items-center justify-center; */
        @apply text-sm font-medium text-neutral-900 transition-colors hover:bg-neutral-200;
        @apply focus-visible:ring focus-visible:ring-neutral-400 focus-visible:ring-offset-2;
    }

    .close {
        @apply absolute right-1.5 top-1.5 flex h-7 w-7 items-center justify-center rounded-full;
        @apply text-neutral-900 transition-colors hover:bg-neutral-500/10;
        @apply focus-visible:ring focus-visible:ring-neutral-400 focus-visible:ring-offset-2;
        @apply bg-white p-0 text-sm font-medium;
    }

    .content {
        @apply z-10 rounded-[4px];
    }
</style>