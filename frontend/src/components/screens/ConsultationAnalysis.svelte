<script lang="ts">
  import clsx from "clsx";

  import { onMount } from "svelte";

  import {
    getApiConsultationUrl,
    getApiQuestionsUrl,
    getConsultationDetailUrl,
  } from "../../global/routes";
  import {
    type ConsultationResponse,
    type DemoOptionsResponse,
    type DemoOptionsResponseItem,
    type QuestionMultiAnswer,
    type QuestionsResponse,
  } from "../../global/types";
  import { getPercentage } from "../../global/utils";
  import { createFetchStore } from "../../global/stores";

  import LoadingMessage from "../LoadingMessage/LoadingMessage.svelte";
  import Chart from "../dashboard/Chart.svelte";
  import MetricsDemoCard from "../dashboard/MetricsDemoCard/MetricsDemoCard.svelte";
  import Panel from "../dashboard/Panel/Panel.svelte";
  import RespondentTopbar from "../dashboard/RespondentTopbar/RespondentTopbar.svelte";
  import TitleRow from "../dashboard/TitleRow.svelte";
  import Finance from "../svg/material/Finance.svelte";
  import PieChart from "../svg/material/PieChart.svelte";

  interface Props {
    consultationId: string;
  }

  let { consultationId = "" }: Props = $props();

  const consultationStore = createFetchStore<ConsultationResponse>();
  const questionsStore = createFetchStore<QuestionsResponse>();
  const demoOptionsStore = createFetchStore<DemoOptionsResponse>();

  let dataRequested: boolean = $state(false);

  let demoCategories = $derived([
    ...new Set(($demoOptionsStore.data || []).map((opt) => opt.name)),
  ]);

  let chartQuestions = $derived(
    $questionsStore.data?.results?.filter(
      (question) => question.has_multiple_choice,
    ),
  );

  function calculateCategoryItems(category: string, demoOptions: DemoOptionsResponseItem[]) {
    const categoryOptions = [...demoOptions].filter(
      (opt: DemoOptionsResponseItem) => opt.name === category,
    );
    
    const total = categoryOptions.reduce(
      (acc: number, opt: DemoOptionsResponseItem) => acc + opt.count,
      0,
    );

    return categoryOptions
      .sort((a: DemoOptionsResponseItem, b: DemoOptionsResponseItem) => {
        return b.count - a.count; // Descending order by count
      })
      .map((demoOption: DemoOptionsResponseItem) => ({
        title: demoOption.value.replaceAll("'", ""),
        count: demoOption.count,
        percentage: getPercentage(demoOption.count, total),
      }));
  }

  let demographicsData = $derived(
    demoCategories.reduce((acc, category) => {
      acc[category] = calculateCategoryItems(category, $demoOptionsStore.data || []);
      return acc;
    }, {} as Record<string, Array<{ title: string; count: number; percentage: number }>>)
  );

  onMount(() => {
    $consultationStore.fetch(getApiConsultationUrl(consultationId));
    $questionsStore.fetch(getApiQuestionsUrl(consultationId));
    $demoOptionsStore.fetch(
      `/api/consultations/${consultationId}/demographic-options/`,
    );
    dataRequested = true;
  });
</script>

<RespondentTopbar
  title="Detailed Consultation Analysis"
  backText="Back to Overview"
  onClickBack={() => (location.href = getConsultationDetailUrl(consultationId))}
/>

<section>
  <Panel>
    <TitleRow
      title="Demographics Breakdown"
      subtitle="Comprehensive view of all demographic categories"
    >
      <Finance slot="icon" />
    </TitleRow>

    {#if !dataRequested || $demoOptionsStore.isLoading}
      <LoadingMessage message="Loading Demographics..." />
    {:else}
      <div class="mb-4 grid grid-cols-12 gap-4">
        {#each demoCategories as category (category)}
          <div class="col-span-12 md:col-span-4">
            <MetricsDemoCard
              title={category}
              items={demographicsData[category]}
              hideThreshold={Infinity}
            />
          </div>
        {/each}
      </div>
    {/if}
  </Panel>
</section>

{#if !dataRequested || $questionsStore.isLoading || $demoOptionsStore.isLoading}
  <LoadingMessage message="Loading Questions..." />
{:else if chartQuestions && chartQuestions?.length > 0}
  <section>
    <Panel>
      <TitleRow
        title="Multiple Choice Questions"
        subtitle="Detailed breakdown of all multiple choice question responses"
      >
        <PieChart slot="icon" />
      </TitleRow>

      <div class="mb-4 grid grid-cols-12 gap-4">
        {#each chartQuestions as question (question.id)}
          <div class="col-span-12 mt-4 sm:col-span-6 lg:col-span-4">
            <div class="h-full w-full">
              <Panel border={true} bg={true}>
                <div class="flex h-full flex-col justify-start">
                  <div class="mb-4 flex items-start gap-4">
                    <span class="text-sm text-primary">
                      Q{question.number}
                    </span>

                    <h3 class="text-xs">
                      {question.question_text}
                    </h3>
                  </div>

                  <div
                    class={clsx([
                      "grow",
                      "flex",
                      "flex-row-reverse",
                      "justify-center",
                      "items-center",
                      "gap-4",
                      "flex-wrap-reverse",
                    ])}
                  >
                    <!-- Container for custom HTML legend -->
                    <div id={"legend-id" + question.number}></div>

                    <div class="h-[6rem]">
                      <Chart
                        legendId={"legend-id" + question.number}
                        labels={question?.multiple_choice_answer?.map(
                          (multiChoiceAnswer: QuestionMultiAnswer) => {
                            return {
                              count: multiChoiceAnswer.response_count,
                              text: multiChoiceAnswer.text,
                            };
                          },
                        ) || []}
                        data={question?.multiple_choice_answer?.map(
                          (multiChoiceAnswer: QuestionMultiAnswer) => {
                            return multiChoiceAnswer.response_count;
                          },
                        ) || []}
                      />
                    </div>
                  </div>
                </div>
              </Panel>
            </div>
          </div>
        {/each}
      </div>
    </Panel>
  </section>
{/if}
