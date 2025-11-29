<script lang="ts">
  import clsx from "clsx";

  import type { Writable } from "svelte/store";

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
  } from "../../global/types";
  import { getPercentage } from "../../global/utils";
  import { createFetchStore } from "../../global/stores";

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

  const { load: loadConsultation }: { load: Function } = createFetchStore();

  const {
    load: loadQuestions,
    data: questionsData,
  }: {
    load: Function;
    data: Writable<ConsultationResponse>;
  } = createFetchStore();

  const {
    load: loadDemoOptions,
    data: demoOptionsData,
  }: {
    load: Function;
    data: Writable<DemoOptionsResponse>;
  } = createFetchStore();

  let totalResponses = $derived(
    $questionsData?.results?.reduce(
      (acc, question) => acc + (question?.total_responses || 0),
      0,
    ),
  );

  let demoCategories = $derived([
    ...new Set(($demoOptionsData || []).map((opt) => opt.name)),
  ]);

  let chartQuestions = $derived(
    $questionsData?.results?.filter((question) => question.has_multiple_choice),
  );

  $effect(() => {
    loadConsultation(getApiConsultationUrl(consultationId));
    loadQuestions(getApiQuestionsUrl(consultationId));
    loadDemoOptions(
      `/api/consultations/${consultationId}/demographic-options/`,
    );
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

    <div class="grid grid-cols-12 gap-4 mb-4">
      {#each demoCategories as category (category)}
        <div class="col-span-12 md:col-span-4">
          <MetricsDemoCard
            title={category}
            items={[...($demoOptionsData || [])]
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
                title: demoOption.value.replaceAll("'", ""),
                count: demoOption.count,
                percentage: getPercentage(demoOption.count, totalResponses),
              }))}
            hideThreshold={Infinity}
          />
        </div>
      {/each}
    </div>
  </Panel>
</section>

{#if chartQuestions?.length > 0}
  <section>
    <Panel>
      <TitleRow
        title="Multiple Choice Questions"
        subtitle="Detailed breakdown of all multiple choice question responses"
      >
        <PieChart slot="icon" />
      </TitleRow>

      <div class="grid grid-cols-12 gap-4 mb-4">
        {#each chartQuestions as question (question.id)}
          <div class="col-span-12 sm:col-span-6 lg:col-span-4 mt-4">
            <div class="w-full h-full">
              <Panel border={true} bg={true}>
                <div class="flex flex-col justify-start h-full">
                  <div class="flex items-start gap-4 mb-4">
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
