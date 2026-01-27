<script lang="ts">
  import clsx from "clsx";

  import { slide } from "svelte/transition";

  import { getPercentage, paginateArray } from "../../../global/utils";
  import type {
    DemoOptionsResponseItem,
    Question,
    QuestionMultiAnswer,
  } from "../../../global/types";

  import TabView from "../../TabView/TabView.svelte";
  import Chart from "../Chart.svelte";
  import MetricsDemoCard from "../MetricsDemoCard/MetricsDemoCard.svelte";
  import MetricsSummary from "../MetricsSummary/MetricsSummary.svelte";
  import Panel from "../Panel/Panel.svelte";
  import TitleRow from "../TitleRow.svelte";
  import Title from "../../Title.svelte";
  import Finance from "../../svg/material/Finance.svelte";
  import LoadingIndicator from "../../LoadingIndicator/LoadingIndicator.svelte";
  import LoadingMessage from "../../LoadingMessage/LoadingMessage.svelte";

  interface Props {
    consultationId: string;
    loading: boolean;
    questions: Question[];
    demoOptions: DemoOptionsResponseItem[];
    demoOptionsLoading: boolean;
  }
  let {
    consultationId = "",
    loading = true,
    questions = [],
    demoOptions = [],
    demoOptionsLoading = true,
  }: Props = $props();

  const itemsPerTab = 3;
  let currPage: number = $state(0);

  const demoOptionCategories = $derived([
    ...new Set(demoOptions?.map((opt) => opt.name)),
  ]);
  const paginatedCategories = $derived(
    paginateArray<string>(demoOptionCategories, itemsPerTab),
  );

  let chartQuestions: Question[] = $derived(
    questions.filter((question: Question) => {
      return question.multiple_choice_answer
        ? question.multiple_choice_answer.length > 0
        : false;
    }),
  );

  let currQuestion: number = $derived(chartQuestions.at(0)?.number || 0);
  let selectedChartQuestion: Question | undefined = $derived(
    chartQuestions.find(
      (chartQuestion) => chartQuestion?.number === currQuestion,
    ),
  );

  let totalResponses = $derived(
    questions?.reduce(
      (acc, question) => acc + (question?.total_responses || 0),
      0,
    ),
  );
</script>

<Panel>
  <div class="my-2">
    <TitleRow title="Key Metrics">
      <Finance slot="icon" />
    </TitleRow>
  </div>

  <div class="grid grid-cols-12 gap-4">
    <div
      class={clsx([
        "col-span-12",
        chartQuestions.length > 0 || loading ? "md:col-span-3" : "h-max",
      ])}
    >
      <Panel bg={true} border={true}>
        <div
          class={clsx([
            "flex",
            "justify-between",
            "max-w-[40rem]",
            "flex-wrap",
            !loading &&
              !chartQuestions.length &&
              "md:w-max md:flex-nowrap md:gap-16",
          ])}
        >
          <MetricsSummary
            questionCount={questions?.length}
            responseCount={totalResponses}
            demoCount={demoOptionCategories.length}
          />
        </div>
      </Panel>
    </div>

    {#if loading || chartQuestions.length > 0}
      <div class={clsx(["col-span-12", "md:col-span-9", "h-full"])}>
        <Panel bg={true} border={true}>
          {#if loading}
            <div class="mb-4">
              <Title level={3} text="Loading questions" />
            </div>

            <LoadingIndicator size="10rem" />
          {:else}
            <TabView
              variant="dots"
              tabs={chartQuestions.map((question: Question) => ({
                title: `Q${question.number}`,
                id: `tab-${question.number}`,
              }))}
              value={`tab-${currQuestion}`}
              handleChange={(newTab) =>
                (currQuestion = parseInt(newTab.replace("tab-", "")))}
            >
              <div slot="title">
                <Title level={3} maxChars={50}>
                  <span class="mr-1 text-primary">
                    Q{selectedChartQuestion?.number}
                  </span>{selectedChartQuestion?.question_text}
                </Title>
              </div>

              <div class="overflow-x-auto">
                <div
                  class="mt-4 flex flex-row-reverse flex-wrap justify-center gap-4"
                >
                  <div id="legend-container"></div>

                  <div class="max-h-[10rem]" data-testid="metrics-chart">
                    <Chart
                      labels={selectedChartQuestion?.multiple_choice_answer?.map(
                        (multiChoiceAnswer: QuestionMultiAnswer) => {
                          return {
                            count: multiChoiceAnswer.response_count,
                            text: multiChoiceAnswer.text,
                          };
                        },
                      ) || []}
                      data={selectedChartQuestion?.multiple_choice_answer?.map(
                        (multiChoiceAnswer: QuestionMultiAnswer) => {
                          return multiChoiceAnswer.response_count;
                        },
                      ) || []}
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

  {#if paginatedCategories.length > 0 && !demoOptionsLoading}
    <div transition:slide class="mt-8">
      <TabView
        variant="dots"
        title="Demographics Breakdown"
        tabs={paginatedCategories.map((_: string[], index: number) => ({
          title: `Demo option category page ${index + 1}`,
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

        <div class="grid grid-cols-12 gap-4 pb-4">
          {#each paginatedCategories[currPage] as category (category)}
            {@const categoryOptions = demoOptions.filter(
              (opt: DemoOptionsResponseItem) => opt.name === category,
            )}

            {@const total = categoryOptions.reduce(
              (acc: number, opt: DemoOptionsResponseItem) => {
                return acc + opt.count;
              },
              0,
            )}

            <MetricsDemoCard
              {consultationId}
              title={category}
              items={[...demoOptions]
                .filter((opt: DemoOptionsResponseItem) => opt.name === category)
                .sort(
                  (a: DemoOptionsResponseItem, b: DemoOptionsResponseItem) => {
                    if (a.count < b.count) {
                      return 1;
                    } else if (a.count > b.count) {
                      return -1;
                    }
                    return 0;
                  },
                )
                .map((demoOption: DemoOptionsResponseItem) => ({
                  title: demoOption.value,
                  count: demoOption.count,
                  percentage: getPercentage(demoOption.count, total),
                }))}
            />
          {/each}
        </div>
      </TabView>
    </div>
  {:else if demoOptionsLoading}
    <LoadingMessage message="Loading Demographics..." />
  {:else}
    <div class="my-4"></div>
  {/if}
</Panel>
