<script lang="ts">
    import clsx from "clsx";

    import { slide, fade, fly } from "svelte/transition";

    import { createTabs, melt } from '@melt-ui/svelte';

    import { writable } from 'svelte/store'


    export let tabs: Tab[] = []; 
    export let value: string = "";
    export let onValueChange: (val: {curr: string, next: string}) => {};

    let prevTabIndex: number = 0;
    let direction: "forward" | "backward" = "forward";
    const writableValue = writable(value);

    $: {
        // Determine navigation direction for fly animation
        const activeTabIndex = tabs.findIndex(tab => tab.id === value);
        direction = activeTabIndex < prevTabIndex ? "backward" : "forward";

        // Update writableValue for the parent
        writableValue.set(value);

        // Keep track of prev tab index for fly animation
        prevTabIndex = tabs.findIndex(tab => tab.id === value);
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
    {#key value}
        <!-- positive x: from right | negative x: from left -->
        <div in:fly={{ x: direction === "forward" ? 300 : -300 }}>
            <slot />
        </div>
    {/key}
</div>