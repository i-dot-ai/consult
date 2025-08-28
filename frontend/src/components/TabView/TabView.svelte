<script lang="ts">
    import clsx from "clsx";

    import { type Component } from "svelte";
    import { writable } from 'svelte/store'
    import { fly } from "svelte/transition";

    import { createTabs, melt } from '@melt-ui/svelte';

    import { TabDirections, TabNames } from "../../global/types";

    import MaterialIcon from "../MaterialIcon.svelte";


    export let tabs: Tab[] = [];
    export let value: string = "";
    export let handleChange = (newVal: TabNames) => {};

    let prevTabIndex: number = tabs.findIndex(tab => tab.id === value);
    let direction: TabDirections = TabDirections.Forward;
    const writableValue = writable(value);

    $: {
        // Determine navigation direction for fly animation
        const activeTabIndex = tabs.findIndex(tab => tab.id === value);

        direction = activeTabIndex > prevTabIndex
            ? TabDirections.Backward
            : TabDirections.Forward;

        // Update writableValue for the parent
        writableValue.set(value);

        // Keep track of prev tab index for fly animation
        prevTabIndex = tabs.findIndex(tab => tab.id === value);
    }

    const {
        elements: { root, list, content, trigger },
    } = createTabs({
        value: writableValue,
        onValueChange: ({ next }) => {
            handleChange(next as TabNames);
            return next;
        },
    });

    interface Tab {
        id: string;
        title: string;
        icon?: Component;
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
                "flex",
                "items-center",
                "justify-between",
                "gap-1",
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
                {#if tab.icon}
                    <MaterialIcon color="fill-neutral-500">
                        <svelte:component this={tab.icon} />
                    </MaterialIcon>
                {/if}

                {tab.title}
            </button>
        {/each}
    </div>

    <!-- Handle which tab to render in parent -->
    {#key value}
        <div in:fly={{ x: direction === TabDirections.Forward ? -300 : 300 }}>
            <slot />
        </div>
    {/key}
</div>