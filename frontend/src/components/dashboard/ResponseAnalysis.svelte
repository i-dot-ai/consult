<script lang="ts">
    import clsx from "clsx";

    import { slide } from "svelte/transition";
    import Button from "../inputs/Button.svelte";
    import TitleRow from "./TitleRow.svelte";
    import Panel from "./Panel.svelte";
    import AnswerCard from "./AnswerCard.svelte";
    import Star from "../svg/material/Star.svelte";
    import Finance from "../svg/material/Finance.svelte";
    import FiltersSidebar from "./FiltersSidebar.svelte";

    export let isAnswersLoading: boolean = true;
    export let answersError: string = "";
    export let answers = [];
    export let hasMorePages: boolean = true;
    export let filteredTotal: number = 0;
    export let handleLoadClick = () => {};

    export let demoOptions: Object = {};
    export let demoData: Object = {};
    export let demoFilters: Object = {};
    export let setDemoFilters: Function = () => {};
</script>

<div class="grid grid-cols-4 gap-4">
    <div class="col-span-4 md:col-span-1">
        <FiltersSidebar {demoOptions} {demoData} {demoFilters} {setDemoFilters} />
    </div>

    <div class="col-span-4 md:col-span-3">
        <section class="my-4">
            <Panel>
                <TitleRow
                    level={2}
                    title="Response refinement"
                    subtitle="In-depth analysis of individual consultation responses."
                >
                    <Finance slot="icon" />
                </TitleRow>

                <section>
                    <TitleRow level={3} title={`Responses (${filteredTotal})`} subtitle="All responses to this question" />

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
                </section>
            </Panel>
        </section>
    </div>
</div>