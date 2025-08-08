<script lang="ts">
    import clsx from "clsx";

    import { slide } from "svelte/transition";
    import Button from "../inputs/Button.svelte";

    export let isAnswersLoading: boolean = true;
    export let answersError: string = "";
    export let answers = [];
    export let hasMorePages: boolean = true;
    export let handleLoadClick = () => {};
</script>

<p>Response Analysis</p>

<section class="my-4">
    {#if isAnswersLoading && answers.length === 0}
        <p>Loading answers...</p>
    {:else if answersError}
        <p>Answers Error: {answersError}</p>
    {:else}
        <ul>
            {#each answers as answer}
                <li>
                    <p class="my-4" transition:slide>{answer.free_text_answer_text}</p>
                </li>
            {/each}
        </ul>

        {#if hasMorePages}
            <div transition:slide class={clsx([
                "transition-all",
                "duration-300",
                "overflow-hidden",
                isAnswersLoading ? "w-[14ch]" : "w-[10ch]",
            ])}>
                <Button fullWidth={true} variant="outline" handleClick={handleLoadClick}>
                    <span class="w-full whitespace-nowrap text-center">
                        {isAnswersLoading ? "Loading answers" : "Load more"}
                    </span>
                </Button>
            </div>
        {/if}
    {/if}
</section>