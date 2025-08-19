<script lang="ts">
    import clsx from "clsx";

    import Title from "../Title.svelte";
    import MaterialIcon from "../MaterialIcon.svelte";
    import type { TitleLevels } from "../../global/types";

    export let title: string = "";
    export let subtitle: string = "";
    export let level: TitleLevels = 2;
</script>

<div class="flex gap-2">
    {#if $$slots.icon}
        <div class="flex justify-center items-center">
            <div class={clsx([
                "bg-pink-50",
                "p-2",
                "rounded-md",
                !subtitle && "mt-1.5",
            ])}>
                <MaterialIcon size="1.3rem" color="fill-pink-700">
                    <slot name="icon" />
                </MaterialIcon>
            </div>
        </div>
    {/if}
    <div class="grow">
        <Title level={level} text={title} />
        {#if subtitle}
            <p class="text-neutral-600 text-sm">
                {subtitle}
            </p>
        {/if}
    </div>

    {#if $$slots.aside}
        <div>
            <slot name="aside" />
        </div>
    {/if}
</div>
