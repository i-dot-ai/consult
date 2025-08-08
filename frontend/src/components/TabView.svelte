<script lang="ts">
    import clsx from "clsx";

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
  class={'flex flex-col overflow-hidden rounded-lg shadow-md w-full'}
>
    <div
        use:melt={$list}
        class={clsx([
            "flex",
            "shrink-0",
            "overflow-x-auto",
            "bg-neutral-100",
        ])}
        aria-label="Question details"
    >
        {#each tabs as tab}
            <button use:melt={$trigger(tab.id)} class={clsx([
                "p-1",
                "trigger",
                "relative",
                "grow",
                "transition-colors",
                "duration-300",
                "cursor-pointer",
                $value === tab.id && "bg-neutral-300",
            ])}>
                {tab.title}
            </button>
        {/each}
    </div>

    {#each tabs as tab}
        <div use:melt={$content(tab.id)} class="grow bg-white p-5">
            <svelte:component this={tab.component} {...(tab.props || {})} />
        </div>
    {/each}
</div>

