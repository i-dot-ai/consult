<script lang="ts">
    import clsx from "clsx";

    import { slide, fade } from "svelte/transition";

    import { createTabs, melt } from '@melt-ui/svelte';

    const {
        elements: { root, list, content, trigger },
        states: { value },
    } = createTabs({
        defaultValue: 'tab-1',
    });

    interface Tab {
        id: string;
        title: string;
        component: any;
        props: Object;
    }
    export let tabs: Tab[] = [];
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
                $value === tab.id && "bg-white",
                "hover:bg-neutral-100",
            ])}>
                {tab.title}
            </button>
        {/each}
    </div>

    {#each tabs as tab}
        {#if tab.id === $value}
            <div transition:slide use:melt={$content(tab.id)} class="grow bg-white">
                <svelte:component this={tab.component} {...(tab.props || {})} />
            </div>
        {/if}
    {/each}
</div>