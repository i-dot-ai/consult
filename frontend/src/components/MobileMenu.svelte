<script lang="ts">
    import { slide } from "svelte/transition";

    import { createDropdownMenu, melt } from "@melt-ui/svelte";

    import clsx from "clsx";

    import MaterialIcon from "./MaterialIcon.svelte";
    import Menu from "./svg/material/Menu.svelte";

    interface NavItem {
        text: string;
        url: string;
    }

    export let items: Array<NavItem> = [];

    const {
        elements: { trigger, menu, item },
        states: { open },
    } = createDropdownMenu({
        forceVisible: false,
        loop: true,
    });
</script>

<div class={clsx([
    "relative",
])}>
    <button use:melt={ $trigger } class={clsx([
        "p-1",
        "border",
        "border-solid",
        "border-white",
        "rounded-md",
        "cursor-pointer",
        "transition-colors",
        "duration-300",
        "hover:bg-primary"
    ])}>
        <MaterialIcon
            size={"1.5rem"}
            color={"fill-white"}
        >
            <Menu />
        </MaterialIcon>
    </button>

    {#if $open}
        <nav use:melt={ $menu } transition:slide>
            <ul  class={clsx([
                "text-white",
                "shadow-xl",
            ])}>
                {#each items as navItem}
                    <li use:melt={ $item } class={clsx([
                        "py-2",
                        "px-4",
                        "transition-colors",
                        "duration-300",
                        window.location.href.includes(navItem.url)
                            ? "bg-gray-800"
                            : "bg-black",
                        "hover:bg-white",
                        "hover:text-black",
                        "cursor-pointer",
                    ])}>
                        <a href={navItem.url}>
                            {navItem.text}
                        </a>
                    </li>
                {/each}
            </ul>
        </nav>
    {/if}
</div>