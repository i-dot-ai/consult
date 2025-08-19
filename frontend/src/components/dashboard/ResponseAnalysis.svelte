<script lang="ts">
    import clsx from "clsx";

    import { slide, fly } from "svelte/transition";
    import Button from "../inputs/Button.svelte";
    import TitleRow from "./TitleRow.svelte";
    import Panel from "./Panel.svelte";
    import AnswerCard from "./AnswerCard.svelte";
    import Finance from "../svg/material/Finance.svelte";
    import FiltersSidebar from "./FiltersSidebar.svelte";
    import Select from "../inputs/Select.svelte";
    import { SearchModeLabels, SearchModeValues } from "../../global/types";
    import Title from "../Title.svelte";
    import TextInput from "../inputs/TextInput.svelte";
    import Alert from "../Alert.svelte";
    import FilterAlt from "../svg/material/FilterAlt.svelte";

    export let isAnswersLoading: boolean = true;
    export let answersError: string = "";
    export let answers = [];
    export let hasMorePages: boolean = true;
    export let filteredTotal: number = 0;
    export let handleLoadClick = () => {};

    export let searchValue: string = "";
    export let setSearchValue = (value: string) => {};
    export let searchMode: SearchModeValues = SearchModeValues.KEYWORD;
    export let setSearchMode = (next: string) => {};

    export let demoOptions: Object = {};
    export let demoData: Object = {};
    export let demoFilters: Object = {};
    export let themeFilters: string[] = [];
    export let setDemoFilters: Function = () => {};
    export let updateThemeFilters: Function = () => {};
    export let themeFiltersApplied: Function = () => {};
    export let demoFiltersApplied: Function = () => {};
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

                <div class="my-8">
                    <div class="mb-2">
                        <Title level={3} text="Search responses:" />
                    </div>

                    {#if demoFiltersApplied(demoFilters) || themeFiltersApplied(themeFilters)}
                        <div transition:fly={{x:300}} class="my-4">
                            <Alert>
                                <FilterAlt slot="icon" />

                                <p slot="text" class="text-sm">
                                    Results are filtered
                                </p>
                            </Alert>
                        </div>
                    {/if}

                    <div class="flex justify-between items-center gap-4">
                        <div class="grow">
                            <TextInput
                                variant="search"
                                id="search-input"
                                label="Search"
                                placeholder="Search..."
                                hideLabel={true}
                                value={searchValue}
                                setValue={(value: string) => setSearchValue(value.trim())}
                            />
                        </div>

                        <Select
                            label="Search Mode"
                            hideLabel={true}
                            value={searchMode}
                            options={[
                                { value: SearchModeValues.KEYWORD, label: SearchModeLabels.KEYWORD },
                                { value: SearchModeValues.SEMANTIC, label: SearchModeLabels.SEMANTIC },
                            ]}
                            handleChange={(nextValue: string) => {
                                setSearchMode(nextValue);
                            }}
                        />
                    </div>
                </div>

                <section>
                    <TitleRow level={3} title={`Responses (${filteredTotal})`} subtitle="All responses to this question" />

                    {#if isAnswersLoading && answers.length === 0}
                        <p transition:slide>Loading answers...</p>
                    {:else if answersError}
                        <p transition:slide>Answers Error: {answersError}</p>
                    {:else}
                        <div>
                            <ul>
                                {#each answers as answer, i (answer.identifier)}
                                    <li>
                                        <div transition:fly={{ x: 300, delay: 100 * i }}>
                                            <AnswerCard
                                                demoData={Object.values(answer.demographic_data)}
                                                multiAnswers={answer.multiple_choice_answer}
                                                evidenceRich={answer.evidenceRich}
                                                id={answer.identifier}
                                                text={answer.free_text_answer_text}
                                                themes={answer.themes}
                                                themeFilters={themeFilters}
                                                handleThemeTagClick={(themeId) => updateThemeFilters(themeId)}
                                            />
                                        </div>
                                    </li>
                                {/each}
                            </ul>

                            <div class="m-auto w-max">
                                {#if hasMorePages}
                                    <div class={clsx([
                                        "transition-all",
                                        "duration-300",
                                        "overflow-hidden",
                                        isAnswersLoading ? "w-[14ch]" : "w-[10ch]",
                                    ])}>
                                        <Button fullWidth={true} handleClick={handleLoadClick}>
                                            <span class="w-full whitespace-nowrap text-center">
                                                {isAnswersLoading ? "Loading answers" : "Load more"}
                                            </span>
                                        </Button>
                                    </div>
                                {/if}
                            </div>
                        </div>
                    {/if}
                </section>
            </Panel>
        </section>
    </div>
</div>