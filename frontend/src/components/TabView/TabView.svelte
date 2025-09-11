<script lang="ts">
    import clsx from "clsx";

    import { type Component } from "svelte";
    import { writable } from 'svelte/store'
    import { fly } from "svelte/transition";

    import { createTabs, melt } from '@melt-ui/svelte';

    import { TabDirections, TabNames } from "../../global/types";

    import MaterialIcon from "../MaterialIcon.svelte";
    import Title from "../Title.svelte";
    import Button from "../inputs/Button/Button.svelte";
    import ArrowForward from "../svg/material/ArrowForward.svelte";


    export let tabs: Tab[] = [];
    export let value: string = "";
    export let handleChange = (newVal: string) => {};
    export let title: string = "";
    export let variant: "default" | "dots" = "default";

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
            handleChange(next);
            return next;
        },
    });

    function incrementTab() {
        const currTabIndex: number = tabs.findIndex(tab => tab.id === $writableValue);
        const nextTabIndex: number = currTabIndex + 1 >= tabs.length
            ? 0
            : currTabIndex + 1

        const newTabId = tabs[nextTabIndex].id;
        writableValue.set(newTabId);
        handleChange(newTabId);
    }

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
    <div class={clsx([
        "flex",
        $$slots.title ? "justify-around" : "justify-center",
        "items-center",
        "gap-4",
        "flex-wrap-reverse",
        "gap-y-2",
    ])}>
        <div class="grow">
            <slot name="title" />
        </div>

        <div
            use:melt={$list}
            class={clsx([
                "flex",
                "items-center",
                "overflow-x-auto",
                "rounded-2xl",
                variant === "default" && "bg-neutral-200",
            ])}
            aria-label="Question details"
        >
            {#if tabs.length > 1 || variant === "default"}
                {#if variant !== "default"}
                    <Button variant="ghost" handleClick={() => incrementTab()}>
                        <MaterialIcon color="fill-neutral-500">
                            <ArrowForward />
                        </MaterialIcon>
                    </Button>
                {/if}

                {#each tabs as tab}
                    {#if variant === "default"}
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
                                <div class="shrink-0">
                                    <MaterialIcon color="fill-neutral-500">
                                        <svelte:component this={tab.icon} />
                                    </MaterialIcon>
                                </div>
                            {/if}

                            {tab.title}
                        </button>
                    {:else if variant === "dots"}
                        <button
                            use:melt={$trigger(tab.id)}
                            class={clsx([
                                "flex",
                                "items-center",
                                "justify-between",
                                "gap-1",
                                "w-2",
                                "h-2",
                                "m-0.5",
                                "p-0",
                                "text-sm",
                                "rounded-2xl",
                                "trigger",
                                "relative",
                                "transition-colors",
                                "duration-300",
                                "cursor-pointer",
                                "bg-neutral-300",
                                $writableValue === tab.id && "bg-primary",
                                "hover:bg-pink-200",
                            ])}
                        ></button>
                    {/if}
                {/each}
            {/if}
        </div>
    </div>

    <!-- Handle which tab to render in parent -->
    {#key value}
        <div in:fly={{ x: direction === TabDirections.Forward ? -300 : 300 }}>
            <slot />
        </div>
    {/key}
</div>