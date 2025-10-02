<script lang="ts">
  import { onMount } from "svelte";
  import { slide } from "svelte/transition";
  import type { Writable } from "svelte/store";

  import TextInput from "../inputs/TextInput/TextInput.svelte";
  import Help from "../svg/material/Help.svelte";
  import Star from "../svg/material/Star.svelte";
  import TitleRow from "../dashboard/TitleRow.svelte";
  import Panel from "../dashboard/Panel/Panel.svelte";
  import QuestionCard from "../dashboard/QuestionCard/QuestionCard.svelte";
  import Metrics from "../dashboard/Metrics/Metrics.svelte";

  import type {
    Consultation,
    DemoOptionsResponse,
  } from "../../global/types.ts";
  import { getApiConsultationUrl } from "../../global/routes.ts";
  import { createFetchStore, favStore } from "../../global/stores.ts";

  export let consultationId: string = "";

  let searchValue: string = "";
  let consultation: Consultation;
  let loading: boolean = true;
  let error: string = "";

  const {
    loading: isDemoOptionsLoading,
    error: demoOptionsError,
    load: loadDemoOptions,
    data: demoOptionsData,
  }: {
    loading: Writable<boolean>;
    error: Writable<string>;
    load: Function;
    data: Writable<DemoOptionsResponse>;
  } = createFetchStore();

  onMount(async () => {
    try {
      const response = await fetch(getApiConsultationUrl(consultationId));
      if (!response.ok) {
        error = "Response not ok";
        return;
      }
      const consultationData = await response.json();
      consultation = consultationData;
      error = "";
    } catch (err: any) {
      error = err.message;
    } finally {
      loading = false;
    }

    loadDemoOptions(
      `/api/consultations/${consultationId}/demographic-options/`,
    );
  });

  $: favQuestions = consultation?.results.filter((question) =>
    $favStore.includes(question.id),
  );

  $: displayQuestions = consultation?.results.filter((question) =>
    `Q${question.number}: ${question.question_text}`
      .toLocaleLowerCase()
      .includes(searchValue.toLocaleLowerCase()),
  );
</script>

<section class="my-8">
  <Metrics
    {consultationId}
    questions={consultation?.results || []}
    {loading}
    demoOptionsLoading={$isDemoOptionsLoading}
    demoOptions={$demoOptionsData || []}
  />
</section>

<section transition:slide class="my-8">
  <div class="my-2">
    <TitleRow title="Favourited questions">
      <Star slot="icon" />
    </TitleRow>
  </div>

  {#if $favStore.length > 0}
    {#if loading}
      <p transition:slide>Loading questions...</p>
    {:else if error}
      <p transition:slide>{error}</p>
    {:else}
      <div transition:slide>
        <div class="mb-8">
          {#each favQuestions as question}
            <QuestionCard
              consultationId={consultationId}
              {question}
              highlightText={searchValue}
              clickable={true}
            />
          {/each}
        </div>
      </div>
    {/if}
  {:else}
    <p transition:slide>You have not favourited any question.</p>
  {/if}
</section>

<section class="my-8">
  <div class="my-2">
    <TitleRow
      title="All consultation questions"
      subtitle="Browse or search through all questions in this consultation."
    >
      <Help slot="icon" />

      <p slot="aside">
        {consultation?.count || 0} questions
      </p>
    </TitleRow>
  </div>

  <Panel bg={true} border={true}>
    {#if loading}
      <p transition:slide>Loading questions...</p>
    {:else if error}
      <p transition:slide>{error}</p>
    {:else}
      <div transition:slide>
        <TextInput
          variant="search"
          id="search-input"
          label="Search"
          placeholder="Search..."
          hideLabel={true}
          value={searchValue}
          setValue={(value) => (searchValue = value.trim())}
        />

        <div class="mb-4">
          {#each displayQuestions as question}
            <QuestionCard
              consultationId={consultationId}
              {question}
              highlightText={searchValue}
              clickable={true}
            />
          {/each}
        </div>
      </div>
    {/if}
  </Panel>
</section>
