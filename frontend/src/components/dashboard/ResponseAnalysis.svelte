<script lang="ts">
    import clsx from "clsx";

    import { slide } from "svelte/transition";
    import Button from "../inputs/Button.svelte";
    import TitleRow from "./TitleRow.svelte";
    import Panel from "./Panel.svelte";
    import AnswerCard from "./AnswerCard.svelte";
    import Star from "../svg/material/Star.svelte";

    export let isAnswersLoading: boolean = true;
    export let answersError: string = "";
    export let answers = [];
    export let hasMorePages: boolean = true;
    export let filteredTotal: number = 0;
    export let handleLoadClick = () => {};
</script>

<section class="my-4">
    <Panel>
        <TitleRow
            level={2}
            title="Response refinement"
            subtitle="Filter and search through individual responses to this question."
        >
            <Star slot="icon" />
        </TitleRow>
    </Panel>
</section>

<section class="my-4">
    <Panel>
        <TitleRow title={`Responses (${filteredTotal})`} subtitle="All responses to this question" level={2} />

        {#if isAnswersLoading && answers.length === 0}
            <p>Loading answers...</p>
        {:else if answersError}
            <p>Answers Error: {answersError}</p>
        {:else}
            <ul>
                {#each answers as answer}
                    <li>
                        <AnswerCard
                            demoData={Object.values(answer.demographic_data)}
                            multiAnswers={answer.multiple_choice_answer}
                            evidenceRich={answer.evidenceRich}
                            id={answer.identifier}
                            text={answer.free_text_answer_text}
                            themes={answer.themes}
                        />
                    </li>
                {/each}
            </ul>

            <div class="m-auto w-max">
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
            </div>
        {/if}
    </Panel>
</section>