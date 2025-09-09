<script lang="ts">
    import clsx from "clsx";

    import type { DemoData, DemoOption, Question } from "../../../global/types";

    import Finance from "../../svg/material/Finance.svelte";
    import TabView from "../../TabView/TabView.svelte";
    import Chart from "../Chart.svelte";
    import MetricsDemoCard from "../MetricsDemoCard/MetricsDemoCard.svelte";
    import MetricsSummary from "../MetricsSummary/MetricsSummary.svelte";
    import Panel from "../Panel/Panel.svelte";
    import TitleRow from "../TitleRow.svelte";
    import Title from "../../Title.svelte";
    import MaterialIcon from "../../MaterialIcon.svelte";
    import ProgressActivity from "../../svg/material/ProgressActivity.svelte";


    interface Props {
        loading: boolean;
        questions: Question[];
        demoOptions: DemoOption[];
    }
    let {
        loading = true,
        questions = [],
        demoOptions = [],
    } = $props();

    const metricsDemo: DemoData = {
        "Respondent Type": {
            "Individual": 2621,
            "Organisation": 1411,
        },
        "Geographic Distribution": {
            "England": 2782,
            "Scotland": 605,
            "Wales": 44,
            "N.Ireland": 61,
        },
        "Self-reported Disability": {
            "No": 2943,
            "Prefer Not to Say": 605,
            "Yes": 484,
        },
    }
    const itemsPerTab = 3;
    let currPage: number = $state(0);

    function paginate(arr: any[], size: number) {
        return arr.reduce((acc, val, i) => {
            let idx = Math.floor(i / size);
            let page = acc[idx] || (acc[idx] = []);
            page.push(val);

            return acc;
        }, [])
    }

    const paginatedDemoKeys = paginate(Object.keys(metricsDemo), itemsPerTab);

    let currQuestion: number = $derived(questions[0]?.number);
    let chartQuestions = $derived(questions.filter(question => question.multiple_choice_options.length > 0));
    let chartQuestion = $derived(chartQuestions.find(question => question.number === currQuestion));

    let totalResponses = $derived(questions?.reduce(
        (acc, question) => acc + question.total_responses,
        0,
    ));
</script>

<Panel>
    <div class="my-2">
        <TitleRow title="Key Metrics">
            <Finance slot="icon" />
        </TitleRow>
    </div>

    <div class="grid grid-cols-12 gap-4">
        <div class={clsx([
            "col-span-12",
            questions.length > 0 || loading ? "md:col-span-3" : "h-max",
        ])}>
            <Panel bg={true} border={true}>
                <div class={clsx([
                    "flex",
                    "justify-between",
                    "max-w-[40rem]",
                    "flex-wrap",
                    !loading && !questions.length && "md:w-max md:gap-16 md:flex-nowrap",
                ])}>
                    <MetricsSummary
                        questionCount={questions?.length}
                        responseCount={totalResponses}
                        demoCount={5}
                    />
                </div>
            </Panel>
        </div>

        {#if loading || questions.length > 0}
            <div class={clsx([
                "col-span-12",
                "md:col-span-9",
                "h-full",
            ])}>
                <Panel bg={true} border={true}>
                    {#if loading}
                        <div class="mb-4">
                            <Title level={3} text={`Loading questions`} />
                        </div>

                        <div
                            style="animation-timing-function: ease-in-out;"
                            class={clsx([
                                "animate-spin",
                                "ease-in-out",
                                "w-max",
                                "m-auto",
                            ])}
                        >
                            <MaterialIcon color="fill-neutral-300" size="10rem">
                                <ProgressActivity />
                            </MaterialIcon>
                        </div>
                    {:else}
                        <TabView
                            variant="dots"
                            tabs={chartQuestions.map(question => ({
                                title: `Q${question.number}`,
                                id: `tab-${question.number}`,
                            }))}
                            value={`tab-${currQuestion}`}
                            handleChange={newTab => currQuestion = parseInt(newTab.replace("tab-", ""))}
                        >
                            <div slot="title">
                                <Title
                                    level={3}
                                    text={`<span class="text-primary mr-1">Q${chartQuestion?.number}</span> ${chartQuestion?.question_text}`}
                                    maxChars={50}
                                />
                            </div>

                            <div class="overflow-x-auto">
                                <div class="h-[10rem] flex flex-row-reverse justify-center gap-4 mt-4">
                                    <div id="legend-container"></div>

                                    <div class="w-max">
                                        <Chart
                                            labels={
                                                chartQuestion?.multiple_choice_options
                                                .map((opt: {text: string, count: number}) => opt.text)
                                            }
                                            data={chartQuestion?.multiple_choice_options.map((_, i) => 100 * (i+1))}
                                        />
                                    </div>
                                </div>
                            </div>
                        </TabView>
                    {/if}
                </Panel>
            </div>
        {/if}
    </div>

    {#if Object.keys(metricsDemo).length > 0}
        <div class="mt-8">
            <TabView
                variant="dots"
                title="Demographics Breakdown"
                tabs={paginatedDemoKeys.map((pageKey: string, index: number) => ({
                    title: pageKey,
                    id: `tab-${index}`,
                }))}
                value={`tab-${currPage}`}
                handleChange={(newTab) => {
                    currPage = parseInt(newTab.replace("tab-", ""));
                }}
            >
                <div slot="title">
                    <Title level={2} text="Demographics Breakdown" />
                </div>

                <div class="grid grid-cols-12 gap-4">
                    {#each paginatedDemoKeys[currPage] as category}
                        <MetricsDemoCard
                            title={category}
                            items={Object.keys(metricsDemo[category]).map(rowKey => ({
                                title: rowKey,
                                count: metricsDemo[category][rowKey],
                                percentage: 67,
                            }))}
                        />
                    {/each}
                </div>
            </TabView>
        </div>
    {/if}
</Panel>