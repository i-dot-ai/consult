<script lang="ts">
    import { slide } from "svelte/transition";
    import { flip } from "svelte/animate";

    import Button from "../inputs/Button.svelte";
    import Title from "../Title.svelte";

    import { getPercentage } from "../../global/utils.ts";

    interface Theme {
        id: string;
        name: string;
        description: string;
        count: number;
    }
    export let themes: Theme[] = [];
    export let totalAnswers: number = 0;
</script>

<div class="w-full overflow-auto">
    <table class="w-full text-md my-8">
        <thead>
            <tr>
                {#each ["Theme", "Mentions", "Percentage", "Actions"] as header}
                    <th class="text-left text-md m-2 pr-4">
                        {header}
                    </th>
                {/each}
            </tr>
        </thead>
        <tbody>
            {#each themes as theme (theme.id)}
                <tr animate:flip={{ duration: 200 }} class="text-xs border-y border-neutral-300 py-2">
                    <td class="pr-4">
                        <div transition:slide class="flex">
                            <div class="flex items-center justify-center p-2">
                                <input type="checkbox" />
                            </div>
                            <div class="py-2">
                                <h3 class="font-bold text-sm">{theme.name}</h3>
                                <p class="text-sm">{theme.description}</p>
                            </div>
                        </div>
                    </td>
                    <td class="pr-4">
                        {theme.count}
                    </td>
                    <td class="pr-4">
                        {getPercentage(theme.count, totalAnswers)}%
                    </td>
                    <td>
                        <Button size="xs" handleClick={() => console.log(theme.id)}>
                            View Responses
                        </Button>
                    </td>
                </tr>
            {/each}
        </tbody>
    </table>
</div>