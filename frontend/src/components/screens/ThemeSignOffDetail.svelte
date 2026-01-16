<script lang="ts">
  import clsx from "clsx";

  import { onMount } from "svelte";
  import { fade, slide } from "svelte/transition";

  import {
    createFetchStore,
    createQueryStore,
    type MockFetch,
  } from "../../global/stores";
  import {
    getApiConfirmSignOffUrl,
    getApiCreateSelectedThemeUrl,
    getApiDeleteSelectedThemeUrl,
    getApiGetGeneratedThemesUrl,
    getApiGetSelectedThemesUrl,
    getApiQuestionUrl,
    getApiSelectGeneratedThemeUrl,
    getApiUpdateSelectedThemeUrl,
    getThemeSignOffUrl,
  } from "../../global/routes";

  import {
    type SelectedThemesDeleteResponse,
    type GeneratedThemesResponse,
    type Question,
    type SelectedThemesResponse,
    type GeneratedTheme,
    type SelectedTheme,
  } from "../../global/types";

  import Panel from "../dashboard/Panel/Panel.svelte";
  import TitleRow from "../dashboard/TitleRow.svelte";
  import Button from "../inputs/Button/Button.svelte";
  import MaterialIcon from "../MaterialIcon.svelte";
  import Price from "../svg/material/Price.svelte";
  import ThemeForm from "../theme-sign-off/ThemeForm/ThemeForm.svelte";
  import QuestionCard from "../dashboard/QuestionCard/QuestionCard.svelte";
  import SelectedThemeCard from "../theme-sign-off/SelectedThemeCard/SelectedThemeCard.svelte";
  import GeneratedThemeCard from "../theme-sign-off/GeneratedThemeCard/GeneratedThemeCard.svelte";
  import CheckCircle from "../svg/material/CheckCircle.svelte";
  import OnboardingTour from "../OnboardingTour/OnboardingTour.svelte";
  import SmartToy from "../svg/material/SmartToy.svelte";
  import Stacks from "../svg/material/Stacks.svelte";
  import Tag from "../Tag/Tag.svelte";
  import Modal from "../Modal/Modal.svelte";
  import Alert from "../Alert.svelte";
  import Target from "../svg/material/Target.svelte";
  import EditSquare from "../svg/material/EditSquare.svelte";
  import ErrorModal, {
    type ErrorType,
  } from "../theme-sign-off/ErrorModal/ErrorModal.svelte";

  interface Props {
    consultationId: string;
    questionId: string;
    questionDataMock?: () => unknown;
    generatedThemesMock?: () => unknown;
    selectedThemesMock?: () => unknown;
    createThemeMock?: () => unknown;
    answersMock?: MockFetch;
    selectGeneratedThemeMock?: () => unknown;
  }

  let {
    consultationId = "",
    questionId = "",
    questionDataMock,
    answersMock,
    selectGeneratedThemeMock,
  }: Props = $props();

  const selectedThemesQuery = $derived(
    createQueryStore<SelectedThemesResponse>(
      getApiGetSelectedThemesUrl(consultationId, questionId),
    ),
  );
  const selectedThemesCreateQuery = $derived(
    createQueryStore(getApiCreateSelectedThemeUrl(consultationId, questionId), {
      method: "POST",
    }),
  );
  const selectedThemesDeleteQuery = $derived(
    createQueryStore<SelectedThemesDeleteResponse>(
      getApiDeleteSelectedThemeUrl(consultationId, questionId, ":themeId"),
      { method: "DELETE" },
    ),
  );
  const generatedThemesQuery = $derived(createQueryStore<GeneratedThemesResponse>(
    getApiGetGeneratedThemesUrl(consultationId, questionId),
  ));
  const generatedThemesSelectQuery = $derived(createQueryStore(
    getApiSelectGeneratedThemeUrl(consultationId, questionId, ":newThemeId"),
    { method: "POST" },
  ));
  const questionQuery = $derived(createQueryStore<Question>(
    getApiQuestionUrl(consultationId, questionId),
  ));
  const confirmSignOffQuery = $derived(
    createQueryStore(getApiConfirmSignOffUrl(consultationId, questionId), {
      method: "PATCH",
    }),
  );

  let isConfirmSignOffModalOpen: boolean = $state(false);
  let addingCustomTheme: boolean = $state(false);

  const flattenGeneratedThemes = (
    items?: GeneratedTheme[],
  ): GeneratedTheme[] => {
    if (!items) {
      return [];
    }
    const result = [];
    for (const item of items) {
      const { children, ...attrs } = item;
      result.push(attrs);
      if (children?.length) {
        result.push(...flattenGeneratedThemes(children));
      }
    }
    return result;
  };

  let flatGeneratedThemes = $derived(
    flattenGeneratedThemes($generatedThemesQuery.data?.results),
  );

  let expandedThemes: string[] = $derived(
    flatGeneratedThemes.map((theme) => theme.id),
  );

  let errorData: ErrorType | null = $state(null);
  let themesBeingSelected: string[] = $state([]); // array of ids
  let dataRequested: boolean = $state(false);

  const errorModalOnClose = () => {
    $selectedThemesQuery.fetch();
    $generatedThemesQuery.fetch();
    errorData = null;
  };

  onMount(() => {
    $selectedThemesQuery.fetch();
    $generatedThemesQuery.fetch();
    $questionQuery.fetch();
    dataRequested = true;
  });

  const createTheme = async (title: string, description: string) => {
    await $selectedThemesCreateQuery.fetch({
      body: {
        name: title,
        description: description,
      },
    });

    $selectedThemesQuery.fetch();
  };

  const removeTheme = async (themeId: string) => {
    const selectedTheme = $selectedThemesQuery.data?.results.find(
      (theme) => theme.id === themeId,
    );

    if (!selectedTheme) {
      console.error(`Selected theme ${themeId} not found`);
      return;
    }

    await $selectedThemesDeleteQuery.fetch({
      headers: {
        "Content-Type": "application/json",
        "If-Match": selectedTheme.version,
      },
      params: { themeId: themeId },
    });

    if (
      !$selectedThemesDeleteQuery.error ||
      $selectedThemesDeleteQuery.status === 404
    ) {
      // No action or error needed if status 404 (theme already deselected)

      $selectedThemesQuery.fetch();
      $generatedThemesQuery.fetch();
    } else if ($selectedThemesDeleteQuery.status === 412) {
      const respData = $selectedThemesDeleteQuery.data;

      errorData = {
        type: "remove-conflict",
        lastModifiedBy: respData?.last_modified_by?.email || "",
        latestVersion: respData?.latest_version || "",
      };
    } else {
      errorData = { type: "unexpected" };
      console.error($selectedThemesDeleteQuery.error);
    }
  };

  const updateTheme = async (
    themeId: string,
    title: string,
    description: string,
  ) => {
    const selectedTheme = $selectedThemesQuery.data?.results.find(
      (theme) => theme.id === themeId,
    );

    if (!selectedTheme) {
      console.error(`Selected theme ${themeId} not found`);
      return;
    }

    try {
      const response = await fetch(
        getApiUpdateSelectedThemeUrl(consultationId, questionId, themeId),
        {
          method: "PATCH",
          headers: {
            "Content-Type": "application/json",
            "If-Match": selectedTheme.version,
          },
          body: JSON.stringify({
            name: title,
            description: description,
          }),
        },
      );

      if (response.ok) {
        $selectedThemesQuery.fetch();
      } else if (response.status === 404) {
        errorData = { type: "theme-does-not-exist" };
      } else if (response.status === 412) {
        const { last_modified_by, latest_version } = await response.json();
        errorData = {
          type: "edit-conflict",
          lastModifiedBy: last_modified_by.email,
          latestVersion: latest_version,
        };
      } else {
        throw new Error(`Edit theme failed: ${response.statusText}`);
      }
    } catch {
      errorData = { type: "unexpected" };
    }
  };

  const handleSelectGeneratedTheme = async (newTheme: GeneratedTheme) => {
    themesBeingSelected = [...themesBeingSelected, newTheme.id];

    await $generatedThemesSelectQuery.fetch({
      params: { newThemeId: newTheme.id },
    });

    await $selectedThemesQuery.fetch();
    await $generatedThemesQuery.fetch();

    themesBeingSelected = themesBeingSelected.filter(
      (themeId) => themeId !== newTheme.id,
    );

    // get selectedtheme_id created after back end select action is complete
    const updatedTheme = flattenGeneratedThemes(
      $generatedThemesQuery.data?.results || [],
    ).find((generatedTheme) => generatedTheme.id === newTheme.id);

    // scroll up to equivalent in selected themes list
    document
      .querySelector(
        `article[data-themeid="${updatedTheme?.selectedtheme_id}"]`,
      )
      ?.scrollIntoView();
  };

  const confirmSignOff = async () => {
    await $confirmSignOffQuery.fetch({
      body: {
        theme_status: "confirmed",
      },
    });

    if ($confirmSignOffQuery.error) {
      isConfirmSignOffModalOpen = false;
      errorData = { type: "unexpected" };
    } else {
      location.replace(getThemeSignOffUrl(consultationId));
    }
  };
  const numSelectedThemesText = (themes?: Array<SelectedTheme>): string => {
    if (!themes?.length) {
      return "";
    }
    return `${themes.length} selected theme${themes.length > 1 ? "s" : ""}`;
  };

  const isThemeExpanded = (themeId: string): boolean => {
    return expandedThemes?.includes(themeId);
  };
  const isAllThemesExpanded = (): boolean => {
    return expandedThemes.length === flatGeneratedThemes.length;
  };
  const expandAllThemes = () => {
    expandedThemes = flatGeneratedThemes.map((theme) => theme.id);
  };
  const collapseAllThemes = () => {
    expandedThemes = [];
  };
  const expandTheme = (themeId: string) => {
    expandedThemes = [...expandedThemes, themeId];
  };
  const collapseTheme = (themeId: string) => {
    expandedThemes = expandedThemes.filter((theme) => theme !== themeId);
  };

  let hasNestedThemes = $derived(
    $generatedThemesQuery.data?.results?.some((theme: GeneratedTheme) =>
      Boolean(theme.children && theme.children.length > 0),
    ),
  );
</script>

<TitleRow
  level={1}
  title="Theme Sign Off"
  subtitle="Finalise themes to use for AI to map responses to"
>
  <Price slot="icon" />

  <div slot="aside">
    <Button
      size="xs"
      handleClick={() => (location.href = getThemeSignOffUrl(consultationId))}
    >
      <span class="p-1"> Choose another question </span>
    </Button>
  </div>
</TitleRow>

<section class="my-8">
  <QuestionCard
    skeleton={$questionQuery.isLoading}
    {consultationId}
    question={$questionQuery.data || {}}
    clickable={false}
  />
</section>

<svelte:boundary>
  <section
    class={clsx([
      "selected-section",
      "my-4",
      "p-4",
      "bg-pink-50/25",
      "rounded-xl",
      "border",
      "border-pink-100",
    ])}
  >
    <div id="onboarding-steps-2-and-3" class="mb-4">
      <Panel variant="primary" bg={true} border={true}>
        <div class="mb-2 flex items-center justify-between">
          <div class="flex items-center gap-2">
            <MaterialIcon color="fill-primary">
              <CheckCircle />
            </MaterialIcon>

            <h3>Selected Themes</h3>

            <Tag variant="primary-light">
              {$selectedThemesQuery.data?.results.length} selected
            </Tag>
          </div>

          <Button
            size="sm"
            handleClick={() => (addingCustomTheme = !addingCustomTheme)}
            highlighted={addingCustomTheme}
            highlightVariant="none"
          >
            <span
              class={clsx([
                "flex",
                "items-center",
                "justify-between",
                "text-primary",
              ])}
            >
              + Add Custom Theme
            </span>
          </Button>
        </div>

        <p class="text-sm text-neutral-500">
          {#if ($selectedThemesQuery.data?.results.length ?? 0) > 0}
            Manage your {numSelectedThemesText(
              $selectedThemesQuery.data?.results,
            )} for the AI in mapping responses. Edit titles and descriptions, or
            add new themes as needed.
          {:else}
            Finalise the themes for the AI to map responses to. Choose from the
            AI generated themes or add new.
          {/if}
        </p>
      </Panel>
    </div>

    {#if addingCustomTheme}
      <div transition:slide>
        <ThemeForm
          handleConfirm={async (title: string, description: string) => {
            await createTheme(title, description);
            addingCustomTheme = false;
          }}
          handleCancel={() => (addingCustomTheme = false)}
        />
      </div>
    {/if}

    {#if $selectedThemesQuery.data?.results.length === 0}
      <div in:fade class="my-8 flex flex-col items-center justify-center gap-2">
        <div class="mb-2">
          <MaterialIcon size="2rem" color="fill-neutral-500">
            <Price />
          </MaterialIcon>
        </div>

        <h3 class="text-md text-neutral-500">No themes selected yet</h3>
        <p class="text-xs text-neutral-500">
          Select themes from the AI-generated suggestions below
        </p>
      </div>
    {:else}
      <div class="mt-4">
        {#each $selectedThemesQuery.data?.results as selectedTheme (selectedTheme.id)}
          <div transition:slide={{ duration: 150 }} class="mb-4 last:mb-0">
            <SelectedThemeCard
              {consultationId}
              {questionId}
              theme={selectedTheme}
              {removeTheme}
              {updateTheme}
              {answersMock}
            />
          </div>
        {/each}
      </div>

      <hr class="my-4" />

      <Button
        variant="primary"
        fullWidth={true}
        disabled={!dataRequested ||
          $selectedThemesQuery.isLoading ||
          $selectedThemesQuery.data?.results.length === 0}
        handleClick={() =>
          (isConfirmSignOffModalOpen = !isConfirmSignOffModalOpen)}
      >
        <div class="flex w-full items-center justify-center gap-2">
          <MaterialIcon color="fill-white">
            <CheckCircle />
          </MaterialIcon>

          <span>
            {#if !dataRequested || $selectedThemesQuery.isLoading}
              Loading Selected Themes
            {:else}
              Sign Off Selected Themes ({$selectedThemesQuery.data?.results
                .length})
            {/if}
          </span>
        </div>
      </Button>
    {/if}

    <Modal
      variant="primary"
      title="Confirm Theme Sign Off"
      icon={CheckCircle}
      open={isConfirmSignOffModalOpen}
      setOpen={(newOpen: boolean) => (isConfirmSignOffModalOpen = newOpen)}
      confirmText="Confirm Sign Off"
      handleConfirm={confirmSignOff}
    >
      <p class="text-sm text-neutral-500">
        Are you sure you want to sign off on these {numSelectedThemesText(
          $selectedThemesQuery.data?.results,
        )} for Question {$questionQuery.data?.number}?
      </p>

      <h4 class="my-4 text-xs font-bold">Selected themes:</h4>

      <div class="max-h-64 overflow-y-auto">
        {#each $selectedThemesQuery.data?.results as selectedTheme (selectedTheme.id)}
          <Panel bg={true} border={false}>
            <h5 class="mb-1 text-xs font-bold">{selectedTheme.name}</h5>
            <p class="text-xs text-neutral-500">{selectedTheme.description}</p>
          </Panel>
        {/each}
      </div>
    </Modal>
  </section>

  {#snippet failed(error)}
    <div>
      {console.error(error)}

      <Panel>
        <Alert>Unexpected selected themes error</Alert>
      </Panel>
    </div>
  {/snippet}
</svelte:boundary>

<div
  class={clsx([
    "relative",
    "w-full",
    "my-8",
    "after:w-full",
    "after:border-b",
    "after:absolute",
    "after:left-0",
    "after:right-0",
    "after:bottom-1/2",
    "after:-z-10",
  ])}
>
  <p
    class={clsx([
      "m-auto",
      "w-max",
      "bg-white",
      "px-4",
      "text-sm",
      "text-neutral-500",
    ])}
  >
    Browse AI Generated Themes
  </p>
</div>

<svelte:boundary>
  <section>
    <Panel>
      <div id="onboarding-step-1">
        <Panel variant="approve" bg={true} border={true}>
          <div class="mb-2 flex items-center justify-between">
            <div class="flex items-center gap-2">
              <MaterialIcon color="fill-secondary">
                <SmartToy />
              </MaterialIcon>

              <h3>AI Generated Themes</h3>

              <Tag variant="success">
                {flattenGeneratedThemes(
                  $generatedThemesQuery.data?.results || [],
                ).length} available
              </Tag>
            </div>

            <div class="flex items-center gap-4">
              {#if hasNestedThemes}
                <div class="flex items-center gap-1 text-xs text-neutral-500">
                  <MaterialIcon color="fill-neutral-500">
                    <Stacks />
                  </MaterialIcon>
                  Multi-level themes
                </div>

                <Button
                  size="sm"
                  disabled={!hasNestedThemes}
                  handleClick={() => {
                    if (isAllThemesExpanded()) {
                      collapseAllThemes();
                    } else {
                      expandAllThemes();
                    }
                  }}
                >
                  <span
                    class={clsx([
                      "flex items-center justify-between gap-1 text-secondary",
                      addingCustomTheme && "text-white",
                    ])}
                  >
                    <MaterialIcon color="fill-secondary">
                      <Stacks />
                    </MaterialIcon>
                    {isAllThemesExpanded() ? "Collapse All" : "Expand All"}
                  </span>
                </Button>
              {/if}
            </div>
          </div>

          <p class="text-sm text-neutral-500">
            Browse AI-generated themes organised by topic hierarchy. Click
            "Select Theme" to add themes to your selected list for analysis.
          </p>
        </Panel>
      </div>

      {#each $generatedThemesQuery.data?.results as theme (theme.id)}
        <GeneratedThemeCard
          {consultationId}
          {questionId}
          {theme}
          {expandedThemes}
          setExpandedThemes={(id) => {
            if (isThemeExpanded(id)) {
              collapseTheme(id);
            } else {
              expandTheme(id);
            }
          }}
          handleSelect={handleSelectGeneratedTheme}
          {answersMock}
          {themesBeingSelected}
        />
      {/each}
    </Panel>
  </section>

  {#if errorData}
    <ErrorModal {...errorData} onClose={errorModalOnClose} />
  {/if}

  {#snippet failed(error)}
    <div>
      {console.error(error)}

      <Panel>
        <Alert>Unexpected generated themes error</Alert>
      </Panel>
    </div>
  {/snippet}
</svelte:boundary>

<svelte:boundary>
  <OnboardingTour
    key="theme-sign-off"
    steps={[
      {
        id: "onboarding-step-1",
        title: "Select Themes",
        body: `Browse the AI-generated themes and click "Select Theme" to move them to your selected themes list. You can view example responses for each theme to understand what types of consultation responses it represents.`,
        icon: Target,
      },
      {
        id: "onboarding-steps-2-and-3",
        title: "Edit & Manage",
        body: "Once themes are selected, you can edit their titles and descriptions by clicking the edit button, or add completely new themes to better organize your analysis.",
        icon: EditSquare,
      },
      {
        id: "onboarding-steps-2-and-3",
        title: "Sign Off & Proceed",
        body: `When you're satisfied with your theme selection and edits, click "Sign Off Selected Themes" to proceed with mapping consultation responses against your finalised themes.`,
        icon: CheckCircle,
      },
    ]}
    resizeObserverTarget={document.querySelector("main")}
  />

  {#snippet failed(error)}
    <div>
      {console.error(error)}

      <Panel>
        <Alert>Unexpected onboarding tour error</Alert>
      </Panel>
    </div>
  {/snippet}
</svelte:boundary>

<style>
  .selected-section :global(div[data-testid="panel-component"]) {
    margin: 0;
  }
</style>
