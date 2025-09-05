<script lang="ts">
    import type { DemoData } from "../../../global/types";

    import Finance from "../../svg/material/Finance.svelte";
    import TabView from "../../TabView/TabView.svelte";
    import Chart from "../Chart.svelte";
    import MetricsDemoCard from "../MetricsDemoCard/MetricsDemoCard.svelte";
    import MetricsSummary from "../MetricsSummary/MetricsSummary.svelte";
    import Panel from "../Panel/Panel.svelte";
    import TitleRow from "../TitleRow.svelte";


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
</script>

<Panel>
    <div class="my-2">
        <TitleRow title="Key Metrics">
            <Finance slot="icon" />
        </TitleRow>
    </div>

    <div class="grid grid-cols-12 gap-4">
        <div class="col-span-12 md:col-span-3">
            <Panel bg={true} border={true}>
                <MetricsSummary
                    questionCount={26}
                    responseCount={107573}
                    demoCount={5}
                />
            </Panel>
        </div>

        <div class="col-span-12 md:col-span-9 h-full">
            <Panel bg={true} border={true}>
                <TabView
                    title="Q3: How important is transparency in AI decision-making processes?"
                    variant="dots"
                    tabs={[
                        { title: "Q3", id: "tab-0" },
                        { title: "Q7", id: "tab-1" },
                        { title: "Q12", id: "tab-2" },
                    ]}
                >
                <div class="overflow-x-auto">
                    <div class="h-[10rem] flex flex-row-reverse justify-around mt-4">
                        <div id="legend-container"></div>
                            <div class="w-max">
                                <Chart
                                    labels={[
                                        "Neutral or uncertain about effectiveness",
                                        "Extremely effective and well structured",
                                        "Completely ineffective and requires overhaul",
                                        "Moderately effective with some improvements needed",
                                        "Somewhat ineffective requiring significant changes",
                                    ]}
                                    data={[
                                        720,
                                        999,
                                        280,
                                        999,
                                        600,
                                    ]}
                                />
                            </div>
                        </div>
                    </div>
                </TabView>
            </Panel>
        </div>
    </div>

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
</Panel>