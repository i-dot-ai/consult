<script lang="ts">
  import clsx from "clsx";

  import { onMount } from "svelte";

  import {
    getApiConsultationUrl,
    getApiConsultationV2Url,
    getApiDemographicOptionsV2Url,
    getApiQuestionsUrl,
    getApiQuestionsV2Url,
    getConsultationDashboardUrl,
  } from "../../../global/routes";
  import {
    type ConsultationResponse,
    type Question,
    type DemoOptionsResponse,
    type DemoOptionsResponseItem,
    type QuestionMultiAnswer,
    type QuestionsResponse,
  } from "../../../global/types";
  import { getPercentage, getDataSetupV2Enabled } from "../../../global/utils";
  import { createFetchStore } from "../../../global/stores";
  import type { ConsultationV2 } from "../../../global/queries/consultations/types";
  import type { QuestionDetailV2 } from "../../../global/queries/questions/types";

  import LoadingMessage from "../../LoadingMessage/LoadingMessage.svelte";
  import Chart from "../../Chart/Chart.svelte";
  import MetricsDemoCard from "../../dashboard/MetricsDemoCard/MetricsDemoCard.svelte";
  import Panel from "../../dashboard/Panel/Panel.svelte";
  import RespondentTopbar from "../../dashboard/RespondentTopbar/RespondentTopbar.svelte";
  import TitleRow from "../../dashboard/TitleRow.svelte";
  import Finance from "../../svg/material/Finance.svelte";
  import PieChart from "../../svg/material/PieChart.svelte";
  import MaterialIcon from "../../MaterialIcon.svelte";
  import Search from "../../svg/material/Search.svelte";

  interface Props {
    consultationId: string;
  }

  let { consultationId = "" }: Props = $props();

  const consultationStore = createFetchStore<
    ConsultationResponse | ConsultationV2
  >();
  const questionsStore = createFetchStore<
    QuestionsResponse | QuestionDetailV2[]
  >();
  const demoOptionsStore = createFetchStore<DemoOptionsResponse>();

  let dataRequested: boolean = $state(false);

  // V2 flag: question list and demographic options come from the v2 API.
  const isV2 = getDataSetupV2Enabled();
  const consultationUrl = isV2
    ? getApiConsultationV2Url(consultationId)
    : getApiConsultationUrl(consultationId);
  const questionsUrl = isV2
    ? getApiQuestionsV2Url(consultationId)
    : getApiQuestionsUrl(consultationId);
  const demoOptionsUrl = isV2
    ? getApiDemographicOptionsV2Url(consultationId)
    : `/api/consultations/${consultationId}/demographics/`;
  const questionText = (question: Question | QuestionDetailV2): string =>
    "question_text" in question
      ? question.question_text
      : (question.text ?? "");

  let demoCategories = $derived([
    ...new Set(($demoOptionsStore.data || []).map((opt) => opt.name)),
  ]);

  let questions = $derived(
    Array.isArray($questionsStore.data)
      ? $questionsStore.data
      : $questionsStore.data?.results || [],
  );

  let chartQuestions = $derived(
    questions.filter((question) =>
      "type" in question
        ? (question.multiple_choice_answer?.length ?? 0) > 0
        : question.has_multiple_choice,
    ),
  );

  function calculateCategoryItems(
    category: string,
    demoOptions: DemoOptionsResponseItem[],
  ) {
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
        id: demoOption.id,
        title: demoOption.value.replaceAll("'", ""),
        count: demoOption.count,
        percentage: getPercentage(demoOption.count, total),
      }));
  }

  function isDemoDataEmpty() {
    return (
      demoCategories.length === 0 ||
      !$demoOptionsStore.data ||
      $demoOptionsStore.data.length === 0
    );
  }

  let demographicsData = $derived(
    demoCategories.reduce(
      (acc, category) => {
        acc[category] = calculateCategoryItems(
          category,
          $demoOptionsStore.data || [],
        );
        return acc;
      },
      {} as Record<
        string,
        Array<{ id: string; title: string; count: number; percentage: number }>
      >,
    ),
  );

  onMount(() => {
    $consultationStore.fetch(consultationUrl);
    $questionsStore.fetch(questionsUrl);
    $demoOptionsStore.fetch(demoOptionsUrl);
    dataRequested = true;
  });
</script>

<RespondentTopbar
  title="Detailed Consultation Analysis"
  backText="Back to Overview"
  onClickBack={() =>
    (location.href = getConsultationDashboardUrl(consultationId))}
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
    {:else if isDemoDataEmpty()}
      <div>
        <div class="flex justify-center mt-12 mb-4">
          <MaterialIcon color="fill-neutral-300" size="3rem">
            <Search />
          </MaterialIcon>
        </div>

        <p class="text-neutral-500 text-center mb-12">No demographics found</p>
      </div>
    {:else}
      <div class="mb-4 grid grid-cols-12 gap-4">
        {#each demoCategories as category (category)}
          <div class="col-span-12 md:col-span-4">
            <MetricsDemoCard
              title={category}
              items={demographicsData[category]}
              hideThreshold={Infinity}
              testId="metrics-summary-{category}"
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
                      {questionText(question)}
                    </h3>
                  </div>

                  <div
                    class={clsx([
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

                    <div class="h-24">
                      <Chart
                        interactive={false}
                        legendId={"legend-id" + question.number}
                        labels={question?.multiple_choice_answer
                          ?.slice()
                          .sort((a, b) => a.text.localeCompare(b.text))
                          .map((multiChoiceAnswer: QuestionMultiAnswer) => {
                            return {
                              count: multiChoiceAnswer.response_count,
                              text: multiChoiceAnswer.text,
                            };
                          }) || []}
                        data={question?.multiple_choice_answer
                          ?.slice()
                          .sort((a, b) => a.text.localeCompare(b.text))
                          .map((multiChoiceAnswer: QuestionMultiAnswer) => {
                            return multiChoiceAnswer.response_count;
                          }) || []}
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
