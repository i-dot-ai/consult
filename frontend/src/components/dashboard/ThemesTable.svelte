<script lang="ts">
    import clsx from "clsx";

    import { fade } from "svelte/transition";
    import { flip } from "svelte/animate";

    import Button from "../inputs/Button/Button.svelte";
    import Title from "../Title.svelte";

    import type { FormattedTheme } from "../../global/types.ts";
    import { getPercentage } from "../../global/utils.ts";

    export let themes: FormattedTheme[] = [];
    export let totalAnswers: number = 0;
    export let skeleton: boolean = false;

    const TABLE_FLIP_SPEED = 10;
</script>

<div class="w-full overflow-auto">
    <table class="w-full text-md my-4">
        <thead class="text-sm">
            <tr>
                {#each ["Theme", "Mentions", "%&nbsp;Percentage" /*, "Actions"*/] as header}
                    <th class="text-left text-md m-2 pr-4 font-normal">
                        {@html header}
                    </th>
                {/each}
            </tr>
        </thead>
        {#if skeleton}
            <tbody in:fade>
                {#each "_".repeat(5) as _}
                    <tr
                        class={clsx([
                            "text-xs",
                            "border-y",
                            "border-neutral-300",
                            "py-2",
                            "transition-colors",
                            "duration-300",
                        ])}
                    >
                        <td class="pr-4">
                            <div transition:fade class="p-2">
                                <h3 class="font-bold text-sm bg-neutral-100 text-neutral-100 select-none w-max mb-2">{"SKELETON ".repeat(3)}</h3>
                                <p class="text-sm bg-neutral-100 text-neutral-100 select-none">{"SKELETON ".repeat(5)}</p>
                            </div>
                        </td>

                        <td class="pr-4">
                            <div class="mt-8">
                                <span class="bg-neutral-100 text-neutral-100 select-none">
                                    000 SKELETON
                                </span>
                            </div>
                        </td>
                        <td class="pr-4">
                            <div class="flex items-center gap-1 mt-8">
                                <span class="w-[5ch] bg-neutral-100 text-neutral-100 select-none">
                                    000%
                                </span>
                            </div>
                        </td>
                    </tr>
                {/each}
            </tbody>
        {:else}
            <tbody in:fade>
                {#each themes as theme (theme.id)}
                    <tr
                        animate:flip={{ duration: 300 + (themes.length * TABLE_FLIP_SPEED) }}
                        class={clsx([
                            "text-xs",
                            "border-y",
                            "border-neutral-300",
                            "py-2",
                            "cursor-pointer",
                            "transition-colors",
                            "duration-300",
                            "hover:bg-neutral-100",
                            theme.highlighted && clsx([
                                "bg-neutral-100",
                                "border-l-4",
                                "border-l-primary",
                            ]),
                        ])}
                        on:click={theme.handleClick}
                        tabindex="0"
                        role="button"
                        aria-pressed={theme.highlighted ? "true" : "false"}
                    >
                        <td class="pr-4">
                            <div transition:fade class="p-2">
                                <h3 class="font-normal text-sm">{theme.name}</h3>
                                <p class="font-light text-sm">{theme.description}</p>
                            </div>
                        </td>
                        <td class="pr-4">
                            {theme.count}
                        </td>
                        <td class="pr-4">
                            <div class="flex items-center gap-1">
                                <span class="w-[5ch]">
                                    {getPercentage(theme.count, totalAnswers)}%
                                </span>
                                <iai-silver-progress-bar
                                    value={getPercentage(theme.count, totalAnswers)}
                                    label=""
                                ></iai-silver-progress-bar>
                            </div>
                        </td>
                        <!-- <td>
                            <Button size="xs" handleClick={() => console.log(theme.id)}>
                                View Responses
                            </Button>
                        </td> -->
                    </tr>
                {/each}
            </tbody>
        {/if}
    </table>
</div>