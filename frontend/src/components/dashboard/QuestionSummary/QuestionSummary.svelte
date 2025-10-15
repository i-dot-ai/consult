<script lang="ts">
  import { slide, fly } from "svelte/transition";

  import {
    TabNames,
    type DemoData,
    type DemoOption,
    type FormattedTheme,
    type QuestionMultiAnswer,
  } from "../../../global/types.ts";
  import { getPercentage } from "../../../global/utils.ts";

  import Lan from "../../svg/material/Lan.svelte";
  import Close from "../../svg/material/Close.svelte";
  import Panel from "../Panel/Panel.svelte";
  import MaterialIcon from "../../MaterialIcon.svelte";
  import Title from "../../Title.svelte";
  import Button from "../../inputs/Button/Button.svelte";
  import TitleRow from "../TitleRow.svelte";
  import ThemesTable from "../ThemesTable/ThemesTable.svelte";
  import FiltersSidebar from "../FiltersSidebar/FiltersSidebar.svelte";
  import Tag from "../../Tag/Tag.svelte";
  import Alert from "../../Alert.svelte";
  import FilterAlt from "../../svg/material/FilterAlt.svelte";

  import {
    themeFilters,
    demoFilters,
    multiAnswerFilters,
  } from "../../../global/state.svelte.ts";
  import NotFoundMessage from "../../NotFoundMessage/NotFoundMessage.svelte";
  import MultiChoice from "../MultiChoice/MultiChoice.svelte";
  import CsvDownload from "../../CsvDownload/CsvDownload.svelte";
  import Finance from "../../svg/material/Finance.svelte";

  interface Props {
    showThemes: boolean;
    themesLoading?: boolean;
    totalAnswers: number;
    filteredTotal: number;
    demoData: DemoData;
    demoOptions: DemoOption;
    themes: FormattedTheme[];
    multiChoice: QuestionMultiAnswer[];
    consultationSlug?: string;
    sortAscending?: boolean;
    searchValue: string;
    evidenceRich: boolean;
    setActiveTab: (newTab: TabNames) => void;
    anyFilterApplied: boolean;
  }
  let {
    showThemes = true,
    themesLoading = true,
    totalAnswers = 0,
    filteredTotal = 0,
    demoData = {},
    demoOptions = {},
    themes = [],
    multiChoice = [],
    consultationSlug = "",
    searchValue = "",
    evidenceRich = false,
    sortAscending = true,
    setActiveTab = () => {},
    anyFilterApplied = false,
  }: Props = $props();
</script>

<div class="grid grid-cols-4 gap-4">
  <div class="col-span-4 md:col-span-1">
    <svelte:boundary>
      <FiltersSidebar
        showEvidenceRich={false}
        {demoOptions}
        {demoData}
        loading={themesLoading}
      />

      {#snippet failed(error)}
        <div>
          {console.error(error)}

          <Panel>
            <Alert>Unexpected Filters Error</Alert>
          </Panel>
        </div>
      {/snippet}
    </svelte:boundary>
  </div>

  <div class="col-span-4 md:col-span-3">
    <svelte:boundary>
      {#if multiChoice && multiChoice.length > 0}
        <MultiChoice data={multiChoice} />
      {/if}

      {#snippet failed(error)}
        <div>{console.error(error)}</div>

        <div class="grow-0">
          <Panel>
            <Alert>Unexpected Multi-Choice Answers Error</Alert>
          </Panel>
        </div>
      {/snippet}
    </svelte:boundary>

    <svelte:boundary>
      {#if showThemes}
        <section class="my-4">
          <Panel>
            <TitleRow
              level={2}
              title="Theme analysis"
              subtitle="Analysis of key themes mentioned in responses to this question."
            >
              <Lan slot="icon" />

              <div slot="aside">
                <svelte:boundary>
                  <CsvDownload
                    fileName={`theme_mentions_for_${consultationSlug}.csv`}
                    data={themes.map((theme) => ({
                      "Theme Name": theme.name,
                      "Theme Description": theme.description,
                      Mentions: theme.count,
                      Percentage: getPercentage(theme.count, totalAnswers),
                    }))}
                  />

                  {#snippet failed(error)}
                    <div>{console.error(error)}</div>
                  {/snippet}
                </svelte:boundary>
              </div>
            </TitleRow>

            {#if anyFilterApplied}
              <div transition:fly={{ x: 300 }} class="my-4">
                <Alert>
                  <FilterAlt slot="icon" />

                  <div
                    class="flex justify-between items-center gap-4 flex-wrap"
                  >
                    <p class="text-sm">Results are filtered</p>

                    <Button
                      variant="primary"
                      size="sm"
                      handleClick={() =>
                        setActiveTab(TabNames.ResponseAnalysis)}
                    >
                      <MaterialIcon>
                        <Finance />
                      </MaterialIcon>

                      {`View Responses${
                        themeFilters.filters.length > 0
                          ? ` (${themeFilters.filters.length} Themes)`
                          : ""
                      }`}
                    </Button>
                  </div>
                </Alert>
              </div>
            {/if}

            {#if themeFilters.applied()}
              <section transition:slide class="my-4">
                <div class="mb-2">
                  <Title
                    level={3}
                    text={`Selected Themes (${themeFilters.filters.length})`}
                  />
                </div>

                <div class="flex gap-1 flex-wrap">
                  {#each themeFilters.filters as themeFilterId (themeFilterId)}
                    <div transition:fly={{ x: 300 }}>
                      <Tag variant="primary">
                        <span>
                          {themes.find((theme) => theme.id === themeFilterId)
                            ?.name || themeFilterId}
                        </span>

                        <Button
                          variant="ghost"
                          size="xs"
                          handleClick={() => themeFilters.update(themeFilterId)}
                        >
                          <MaterialIcon color="fill-white">
                            <Close />
                          </MaterialIcon>
                        </Button>
                      </Tag>
                    </div>
                  {/each}
                </div>
              </section>
            {/if}

            {#if themes.length === 0 && !themesLoading}
              <NotFoundMessage
                title="No themes found"
                body="Try adjusting your search terms or filters."
              />
            {:else}
              <Panel>
                <ThemesTable
                  themes={[...themes].sort((a, b) =>
                    sortAscending ? a.count - b.count : b.count - a.count,
                  )}
                  {totalAnswers}
                  skeleton={themesLoading}
                />
              </Panel>
            {/if}

            <div class="flex justify-between items-center flex-wrap gap-y-4">
              <small>
                {`Showing ${themes?.length || 0} themes • Click rows to select themes for response analysis`}
              </small>

              <div class="flex items-center gap-1">
                <small>Order:</small>
                <Button
                  size="xs"
                  highlighted={!sortAscending}
                  handleClick={() => (sortAscending = false)}
                >
                  High to Low
                </Button>
                <Button
                  size="xs"
                  highlighted={sortAscending}
                  handleClick={() => (sortAscending = true)}
                >
                  Low to High
                </Button>
              </div>
            </div>
          </Panel>
        </section>
      {/if}

      {#snippet failed(error)}
        <div>
          {console.error(error)}

          <Panel>
            <Alert>Unexpected Themes Table Error</Alert>
          </Panel>
        </div>
      {/snippet}
    </svelte:boundary>
  </div>
</div>
