<script lang="ts">
    import clsx from "clsx";

    import { slide, fade } from "svelte/transition";

    import { createTabs, melt } from '@melt-ui/svelte';

    import { writable } from 'svelte/store'


    export let tabs: Tab[] = []; 
    export let value: string = "";
    export let onValueChange: (val: {curr: string, next: string}) => {};

    const writableValue = writable(value);
    $: {
        writableValue.set(value);
    }

    const {
        elements: { root, list, content, trigger },
    } = createTabs({
        value: writableValue,
        onValueChange: onValueChange,
    });

    interface Tab {
        id: string;
        title: string;
        component: any;
        props: Object;
    }
</script>

<div
    use:melt={$root}
    class={clsx([
        "flex",
        "flex-col",
        "overflow-hidden"
    ])}
>
    <div
        use:melt={$list}
        class={clsx([
            "flex",
            "overflow-x-auto",
            "m-auto",
            "rounded-2xl",
            "bg-neutral-200",
        ])}
        aria-label="Question details"
    >
        {#each tabs as tab}
            <button use:melt={$trigger(tab.id)} class={clsx([
                "m-1",
                "py-1",
                "px-2",
                "text-sm",
                "rounded-2xl",
                "trigger",
                "relative",
                "transition-colors",
                "duration-300",
                "cursor-pointer",
                $writableValue === tab.id && "bg-white",
                "hover:bg-neutral-100",
            ])}>
                {tab.title}
            </button>
        {/each}
    </div>

    <!-- Handle which tab to render in parent -->
    <slot />
</div>