<script lang="ts">
  import clsx from "clsx";

  import { slide, fly, fade } from "svelte/transition";
  import Button from "../../inputs/Button/Button.svelte";
  import TitleRow from "../TitleRow.svelte";
  import Panel from "../Panel/Panel.svelte";
  import AnswerCard from "../AnswerCard/AnswerCard.svelte";
  import Finance from "../../svg/material/Finance.svelte";
  import FiltersSidebar from "../FiltersSidebar/FiltersSidebar.svelte";
  import Select from "../../inputs/Select/Select.svelte";

  import {
    SearchModeLabels,
    SearchModeValues,
    type DemoData,
    type DemoOption,
    type DemoOptionsResponse,
    type ResponseAnswer,
    type ResponseTheme,
    type SearchableSelectOption,
  } from "../../../global/types";
  import { themeFilters } from "../../../global/state.svelte";
  import { updateResponseReadStatus } from "../../../global/routes";

  import Title from "../../Title.svelte";
  import TextInput from "../../inputs/TextInput/TextInput.svelte";
  import Alert from "../../Alert.svelte";
  import FilterAlt from "../../svg/material/FilterAlt.svelte";
  import SearchableSelect from "../../inputs/SearchableSelect.svelte";
  import Tag from "../../Tag/Tag.svelte";
  import MaterialIcon from "../../MaterialIcon.svelte";
  import Close from "../../svg/material/Close.svelte";
  import Popover from "../../inputs/Popover/Popover.svelte";
  import NotFoundMessage from "../../NotFoundMessage/NotFoundMessage.svelte";
  import Flag2 from "../../svg/material/Flag2.svelte";
  import { onDestroy } from "svelte";

  export let consultationId: string = "";
  export let questionId: string = "";
  export let pageSize: number = 5;
  export let isAnswersLoading: boolean = true;
  export let isThemesLoading: boolean = true;
  export let answersError: string | null = "";
  export let answers: ResponseAnswer[] = [];
  export let hasMorePages: boolean = true;
  export let filteredTotal: number = 0;
  export let handleLoadClick = () => {};
  export let resetData = () => {};

  export let searchValue: string = "";
  export let setSearchValue = (_value: string) => {};
  export let searchMode: SearchModeValues = SearchModeValues.KEYWORD;
  export let setSearchMode = (_searchMode: SearchModeValues) => {};

  export let demoOptions: DemoOption = {};
  export let demoData: DemoData = {};
  export let demoOptionsData: DemoOptionsResponse = [];
  export let themes: ResponseTheme[] = [];

  export let evidenceRich: boolean = false;
  export let setEvidenceRich = () => {};

  export let unseenResponses: boolean = false;
  export let setUnseenResponses = () => {};

  export let flaggedOnly: boolean = false;
  export let setFlaggedOnly: (newVal: boolean) => void = () => {};

  export let anyFilterApplied: boolean = false;
  export let resetFilters: () => void = () => {};

  const BASE_FLY_DELAY = 100;

  function getDelay(index: number): number {
    // Reset delay after page size so load more button loads
    // new answers without initial delay but still scattered
    return BASE_FLY_DELAY * (index % pageSize);
  }

  let markAsReadTimer: ReturnType<typeof setTimeout> | null = null;

  function startMarkAsReadTimer() {
    if (markAsReadTimer) {
      clearTimeout(markAsReadTimer);
    }

    const READ_TIMEOUT = 10000; // 10 seconds

    markAsReadTimer = setTimeout(async () => {
      if (answers.length > 0) {
        const markPromises = answers.map((answer) =>
          fetch(updateResponseReadStatus(consultationId, answer.id), {
            method: "POST",
          }),
        );
        await Promise.all(markPromises);
      }
    }, READ_TIMEOUT);
  }

  function resetMarkAsReadTimer() {
    if (markAsReadTimer) {
      clearTimeout(markAsReadTimer);
      markAsReadTimer = null;
    }
  }

  onDestroy(() => {
    resetMarkAsReadTimer();
  });

  $: if (answers.length > 0 && !isAnswersLoading && !answersError) {
    startMarkAsReadTimer();
  }

  $: if (
    searchValue ||
    anyFilterApplied ||
    evidenceRich ||
    unseenResponses ||
    flaggedOnly ||
    themeFilters.filters.length > 0
  ) {
    resetMarkAsReadTimer();
  }
</script>

<div class="grid grid-cols-4 gap-4">
  <div class="col-span-4 md:col-span-1">
    <svelte:boundary>
      <FiltersSidebar
        showEvidenceRich={true}
        showUnseenResponse={false}
        {demoOptions}
        {demoData}
        {demoOptionsData}
        {evidenceRich}
        {setEvidenceRich}
        {unseenResponses}
        {setUnseenResponses}
        loading={isThemesLoading}
      />

      {#snippet failed(error)}
        <div>
          {console.error(error)}

          <Panel>
            <Alert>Unexpected filters error</Alert>
          </Panel>
        </div>
      {/snippet}
    </svelte:boundary>
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

        <svelte:boundary>
          <div class="mt-8 px-4">
            <div class="mb-2">
              <Title level={3} text="Search responses:" />
            </div>

            {#if anyFilterApplied}
              <div transition:fly={{ x: 300 }} class="my-4">
                <Alert>
                  <FilterAlt slot="icon" />

                  <p class="text-sm">Results are filtered</p>
                </Alert>
              </div>
            {/if}

            <div
              class="flex flex-col-reverse items-center justify-between gap-4 sm:flex-row"
            >
              <div class="w-full grow sm:w-auto">
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

              <div class="w-full sm:w-auto">
                <Select
                  id="search_mode"
                  label="Search Mode"
                  hideLabel={true}
                  value={searchMode}
                  items={[
                    {
                      value: SearchModeValues.KEYWORD,
                      label: SearchModeLabels.KEYWORD,
                    },
                    {
                      value: SearchModeValues.SEMANTIC,
                      label: SearchModeLabels.SEMANTIC,
                    },
                  ]}
                  onchange={(nextValue: string) => {
                    setSearchMode(nextValue as SearchModeValues);
                  }}
                />
              </div>
            </div>
          </div>

          {#snippet failed(error)}
            <div>
              {console.error(error)}

              <Panel>
                <Alert>Unexpected search bar error</Alert>
              </Panel>
            </div>
          {/snippet}
        </svelte:boundary>

        <section>
          <svelte:boundary>
            <div class="my-8">
              <Panel bg={true}>
                <Title level={3} text="Show responses by themes:"></Title>

                {#if themeFilters.filters.length > 0}
                  <div
                    transition:slide
                    class="my-2 flex flex-wrap items-center gap-2"
                  >
                    {#each themeFilters.filters as themeFilter (themeFilter)}
                      <div transition:fly={{ x: 300 }}>
                        <Tag variant="primary">
                          <span>
                            {themes.find((theme) => theme.id === themeFilter)
                              ?.name}
                          </span>

                          <div class="self-center">
                            <Button
                              variant="ghost"
                              size="xs"
                              handleClick={() =>
                                themeFilters.update(themeFilter)}
                            >
                              <MaterialIcon color="fill-white">
                                <Close />
                              </MaterialIcon>
                            </Button>
                          </div>
                        </Tag>
                      </div>
                    {/each}
                  </div>
                {/if}

                <div class="mt-4 w-full md:w-1/2">
                  <Popover>
                    <span slot="trigger" class="block text-left">
                      Select Themes...
                    </span>

                    <div slot="panel" class="w-full bg-white p-4 shadow-lg">
                      <SearchableSelect
                        handleChange={(option: SearchableSelectOption) => {
                          const newValue = (option.value as { value: string })?.value;
                          if (newValue) {
                            themeFilters.update(newValue);
                          }
                        }}
                        options={themes.map((theme) => ({
                          value: theme.id,
                          label: theme.name,
                          description: theme.description,
                          disabled: false,
                        }))}
                        hideArrow={true}
                        selectedValues={themeFilters.filters}
                      />
                    </div>
                  </Popover>
                </div>
              </Panel>
            </div>

            {#snippet failed(error)}
              <div>
                {console.error(error)}

                <Panel>
                  <Alert>Unexpected themes filter error</Alert>
                </Panel>
              </div>
            {/snippet}
          </svelte:boundary>
        </section>

        <section>
          <svelte:boundary>
            <TitleRow
              level={3}
              title={`${filteredTotal} responses found`}
              subtitle="All responses to this question"
            >
              <div slot="aside" class="flex flex-wrap items-center gap-2">
                {#if anyFilterApplied}
                  <Button
                    size="sm"
                    handleClick={() => {
                      resetFilters();
                    }}
                  >
                    Clear filters
                  </Button>
                {/if}

                <Button
                  size="sm"
                  highlightVariant="primary"
                  highlighted={flaggedOnly}
                  handleClick={() => setFlaggedOnly(!flaggedOnly)}
                >
                  <MaterialIcon
                    color={flaggedOnly ? "fill-white" : "fill-neutral-700"}
                  >
                    <Flag2 />
                  </MaterialIcon>

                  Flagged only
                </Button>
              </div>
            </TitleRow>

            {#if isAnswersLoading && answers.length === 0}
              <div transition:fade>
                {#each "_".repeat(5) as _, i (i)}
                  <AnswerCard skeleton={true} />
                {/each}
              </div>
            {:else if answersError}
              <div transition:slide class="my-2">
                <Alert>
                  <span class="text-sm">
                    Answers Error: {answersError}
                  </span>
                </Alert>
              </div>
            {:else}
              <div>
                <ul>
                  {#each answers as answer, i (answer.id)}
                    <li>
                      <div transition:fly={{ x: 300, delay: getDelay(i) }}>
                        <AnswerCard
                          {consultationId}
                          {questionId}
                          answerId={answer.id}
                          respondentId={answer.respondent_id}
                          respondentDisplayId={answer.identifier.toString()}
                          demoData={Object.values(answer.demographic_data)}
                          multiAnswers={answer.multiple_choice_answer}
                          evidenceRich={answer.evidenceRich}
                          text={answer.free_text_answer_text}
                          themes={answer.themes || []}
                          themeOptions={themes}
                          highlightText={searchValue}
                          isFlagged={answer.is_flagged}
                          isEdited={answer.is_edited}
                          {resetData}
                        />
                      </div>
                    </li>
                  {/each}
                </ul>

                {#if answers.length === 0}
                  <div transition:fade>
                    <NotFoundMessage
                      title="No responses found"
                      body="Try adjusting your search terms or filters."
                    />
                  </div>
                {/if}

                {#if isAnswersLoading}
                  <div transition:fade>
                    {#each "_".repeat(5) as _, i (i)}
                      <AnswerCard skeleton={true} />
                    {/each}
                  </div>
                {/if}

                <div class="m-auto w-max">
                  {#if hasMorePages}
                    <div
                      class={clsx([
                        "transition-all",
                        "duration-300",
                        "overflow-hidden",
                        isAnswersLoading ? "w-[14ch]" : "w-[10ch]",
                      ])}
                    >
                      <Button
                        fullWidth={true}
                        handleClick={handleLoadClick}
                        size="sm"
                      >
                        <span class="w-full whitespace-nowrap text-center">
                          {isAnswersLoading ? "Loading answers" : "Load more"}
                        </span>
                      </Button>
                    </div>
                  {/if}
                </div>

                {#if answers}
                  <p class="mt-2 text-center text-sm">
                    {`Showing first ${answers.length} of ${filteredTotal} responses. Use filters to narrow results.`}
                  </p>
                {/if}
              </div>
            {/if}

            {#snippet failed(error)}
              <div>
                {console.error(error)}

                <Panel>
                  <Alert>Unexpected answers list error</Alert>
                </Panel>
              </div>
            {/snippet}
          </svelte:boundary>
        </section>
      </Panel>
    </section>
  </div>
</div>
