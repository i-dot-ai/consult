<script lang="ts">
  import { onMount } from "svelte";
  import { slide } from "svelte/transition";
  import type { Writable } from "svelte/store";

  import TextInput from "../inputs/TextInput/TextInput.svelte";
  import Help from "../svg/material/Help.svelte";
  import TitleRow from "../dashboard/TitleRow.svelte";
  import Panel from "../dashboard/Panel/Panel.svelte";
  import QuestionCard from "../dashboard/QuestionCard/QuestionCard.svelte";

  import {
    getApiQuestionsUrl,
    getThemeSignoffDetailUrl,
  } from "../../global/routes.ts";
  import { createFetchStore } from "../../global/stores.ts";
  import Tag from "../Tag/Tag.svelte";
  import MaterialIcon from "../MaterialIcon.svelte";
  import Checklist from "../svg/material/Checklist.svelte";

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
              clickable={question.has_free_text}
              disabled={!question.has_free_text}
              url={getThemeSignoffDetailUrl(consultationId, question.id)}
              subtext={!question.has_free_text
                ? "No free text responses for this question = no themes to sign off. Multiple choice data will be shown in analysis dashboard."
                : undefined}
            >
              {#snippet tag()}
                {#if !question.has_free_text}
                  <Tag variant="primary-light">
                    <MaterialIcon color="fill-primary">
                      <Checklist />
                    </MaterialIcon>

                    Multiple choice
                  </Tag>
                {:else if question.theme_status === "confirmed"}
                  <Tag variant="primary-light">Signed off</Tag>
                {:else}
                  <div></div>
                {/if}
              {/snippet}
            </QuestionCard>
          {/each}
        </div>
      </div>
    {/if}
  </Panel>
</section>
