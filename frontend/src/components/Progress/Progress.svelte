<script lang="ts">
    // Using melt-ui progress
    // Docs: https://www.melt-ui.com/docs/builders/progress

    import { createProgress, melt } from '@melt-ui/svelte';
    import clsx from 'clsx';
    import { writable } from 'svelte/store';


    export let value: number = 0;

    const writableValue = writable(30);

    $: writableValue.set(value);


    const {
        elements: { root },
        options: { max },
    } = createProgress({
        value: writableValue,
        max: 100,
    });
</script>

<div
    use:melt={$root}
    class={clsx([
        "relative",
        "h-2",
        "w-full",
        "overflow-hidden",
        "rounded-[99999px]",
        "bg-neutral-300",
    ])}
>
    <div
        class={clsx([
            "h-full",
            "w-full",
            "bg-primary",
            "transition-transform",
            "duration-[660ms]",
            "ease-[cubic-bezier(0.65,0,0.35,1)]",
        ])}
        style={`transform: translateX(-${
            100 - (100 * ($writableValue ?? 0)) / ($max ?? 1)
        }%)`}
    ></div>
</div>