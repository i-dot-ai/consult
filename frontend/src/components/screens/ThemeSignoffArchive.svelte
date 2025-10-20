<script lang="ts">
  import { onMount } from "svelte";
  import { slide } from "svelte/transition";
  import type { Writable } from "svelte/store";

  import TextInput from "../inputs/TextInput/TextInput.svelte";
  import Help from "../svg/material/Help.svelte";
  import TitleRow from "../dashboard/TitleRow.svelte";
  import Panel from "../dashboard/Panel/Panel.svelte";
  import QuestionCard from "../dashboard/QuestionCard/QuestionCard.svelte";

  import { getApiQuestionsUrl, getThemeSignoffDetailUrl } from "../../global/routes.ts";
  import { createFetchStore } from "../../global/stores.ts";

  export let consultationId: string = "";

  let searchValue: string = "";

  const {
    loading: isQuestionsLoading,
    error: questionsError,
    load: loadQuestions,
    data: questionsData,
  }: {
    loading: Writable<boolean>;
    error: Writable<string>;
    load: Function;
    data: Writable<any>;
  } = createFetchStore();

  onMount(async () => {
    loadQuestions(getApiQuestionsUrl(consultationId));
  });  

  $: displayQuestions = $questionsData?.results?.filter((question) =>
    `Q${question.number}: ${question.question_text}`
      .toLocaleLowerCase()
      .includes(searchValue.toLocaleLowerCase()),
  );
</script>

<section class="my-8">
  <div class="my-2">
    <TitleRow
      title="All consultation questions"
      subtitle="Browse or search through all questions in this consultation."
    >
      <Help slot="icon" />

      <p slot="aside">
        {$questionsData?.results?.length || 0} questions
      </p>
    </TitleRow>
  </div>

  <Panel bg={true} border={true}>
    {#if $isQuestionsLoading}
      <p transition:slide>Loading questions...</p>
    {:else if $questionsError}
      <p transition:slide>{$questionsError}</p>
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
              {consultationId}
              {question}
              highlightText={searchValue}
              clickable={true}
              url={getThemeSignoffDetailUrl(consultationId, question.id)}
              isSignedOff={question.theme_status === "confirmed"}
            />
          {/each}
        </div>
      </div>
    {/if}
  </Panel>
</section>
