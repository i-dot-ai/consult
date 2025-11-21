<script lang="ts">
  import clsx from "clsx";

  import { onMount } from "svelte";
  import { fade, slide } from "svelte/transition";

  import { createFetchStore } from "../../global/stores";
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
  import { flattenArray } from "../../global/utils";

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
  } from "../theme-sign-off/ErrorModal.svelte";

  let {
    consultationId = "",
    questionId = "",
    questionDataMock,
    generatedThemesMock,
    selectedThemesMock,
    createThemeMock,
    answersMock,
    selectGeneratedThemeMock,
  } = $props();

  const selectedThemesStore = createFetchStore(selectedThemesMock);
  const selectedThemesCreateStore = createFetchStore(createThemeMock);
  const selectedThemesDeleteStore = createFetchStore();
  const generatedThemesStore = createFetchStore(selectedThemesMock);
  const generatedThemesSelectStore = createFetchStore(selectGeneratedThemeMock);
  const questionStore = createFetchStore(questionDataMock);
  const confirmSignOffStore = createFetchStore();

  let isConfirmSignOffModalOpen = $state(false);
  let addingCustomTheme = $state(false);
  let expandedThemes: string[] = $state([]);
  let errorData: ErrorType | null = $state(null);
  let themesBeingSelected = $state([]);
  let dataRequested: boolean = $state(false);

  let flatGeneratedThemes = $derived(
    flattenArray($generatedThemesStore.data?.results),
  );

  const errorModalOnClose = () => {
    $selectedThemesStore.fetch(getApiGetSelectedThemesUrl(consultationId, questionId));
    $generatedThemesStore.fetch(
      getApiGetGeneratedThemesUrl(consultationId, questionId),
    );
    errorData = null;
  };

  $effect(() => {
    expandedThemes = flatGeneratedThemes.map((theme) => theme.id);
  });

  onMount(() => {
    $selectedThemesStore.fetch(getApiGetSelectedThemesUrl(consultationId, questionId));
    $generatedThemesStore.fetch(
      getApiGetGeneratedThemesUrl(consultationId, questionId),
    );
    $questionStore.fetch(getApiQuestionUrl(consultationId, questionId));
    dataRequested = true;
  });

  const createTheme = async (title: string, description: string) => {
    await $selectedThemesCreateStore.fetch(
      getApiCreateSelectedThemeUrl(consultationId, questionId),
      "POST",
      {
        name: title,
        description: description,
      },
    );

    $selectedThemesStore.fetch(getApiGetSelectedThemesUrl(consultationId, questionId));
  };

  const removeTheme = async (themeId: string) => {
    const selectedTheme = $selectedThemesStore.data?.results.find(
      (theme) => theme.id === themeId,
    );

    await $selectedThemesDeleteStore.fetch(
      getApiDeleteSelectedThemeUrl(consultationId, questionId, themeId),
      "DELETE",
      undefined,
      {
        "Content-Type": "application/json",
        "If-Match": selectedTheme.version,
      },
    );

    if (!$selectedThemesDeleteStore.error || $selectedThemesDeleteStore.status === 404) {
      // No action or error needed if status 404 (theme already deselected)

      $selectedThemesStore.fetch(
        getApiGetSelectedThemesUrl(consultationId, questionId),
      );
      $generatedThemesStore.fetch(
        getApiGetGeneratedThemesUrl(consultationId, questionId),
      );
    } else if ($selectedThemesDeleteStore.status === 412) {
      const { last_modified_by, latest_version } = $selectedThemesDeleteStore.data;
      errorData = {
        type: "remove-conflict",
        lastModifiedBy: last_modified_by.email,
        latestVersion: latest_version,
      };
    } else {
      errorData = { type: "unexpected" };
      console.error($selectedThemesDeleteStore.error);
    }
  };

  const updateTheme = async (
    themeId: string,
    title: string,
    description: string,
  ) => {
    const selectedTheme = $selectedThemesStore.data?.results.find(
      (theme) => theme.id === themeId,
    );

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
        $selectedThemesStore.fetch(
          getApiGetSelectedThemesUrl(consultationId, questionId),
        );
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
    } catch (err: any) {
      errorData = { type: "unexpected" };
    }
  };

  const handleSelectGeneratedTheme = async (newTheme) => {
    themesBeingSelected = [...themesBeingSelected, newTheme.id];

    await $generatedThemesSelectStore.fetch(
      getApiSelectGeneratedThemeUrl(consultationId, questionId, newTheme.id),
      "POST",
    );

    await $selectedThemesStore.fetch(
      getApiGetSelectedThemesUrl(consultationId, questionId),
    );
    await $generatedThemesStore.fetch(
      getApiGetGeneratedThemesUrl(consultationId, questionId),
    );

    themesBeingSelected = themesBeingSelected.filter(themeId => themeId !== newTheme.id);

    // get selectedtheme_id created after back end select action is complete
    const updatedTheme = flattenArray($generatedThemesStore.data?.results || []).find(
      (generatedTheme) => generatedTheme.id === newTheme.id,
    );

    // scroll up to equivalent in selected themes list
    document
      .querySelector(`article[data-themeid="${updatedTheme.selectedtheme_id}"]`)
      ?.scrollIntoView();
  };

  const confirmSignOff = async () => {
    await $confirmSignOffStore.fetch(
      getApiConfirmSignOffUrl(consultationId, questionId),
      "PATCH",
      {
        theme_status: "confirmed",
      },
    );

    if ($confirmSignOffStore.error) {
      isConfirmSignOffModalOpen = false;
      errorData = { type: "unexpected" };
    } else {
      location.replace(getThemeSignOffUrl(consultationId));
    }
  };
  const numSelectedThemesText = (themes?: Array<any>): string => {
    if (!themes) {
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
      >Choose another question</Button
    >
  </div>
</TitleRow>

<section class="my-8">
  <QuestionCard
    skeleton={$isQuestionLoading}
    {consultationId}
    question={$questionData || {}}
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
        <div class="flex items-center justify-between mb-2">
          <div class="flex items-center gap-2">
            <MaterialIcon color={"fill-primary"}>
              <CheckCircle />
            </MaterialIcon>

            <h3>Selected Themes</h3>

            <Tag variant="primary-light">
              {$selectedThemesStore.data?.results.length} selected
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

        <p class="text-neutral-500 text-sm">
          Manage your {numSelectedThemesText($selectedThemesStore.data?.results)} for the
          AI in mapping responses. Edit titles and descriptions, or add new themes
          as needed.
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

    {#if $selectedThemesStore.data?.results.length === 0}
      <div in:fade class="flex items-center justify-center flex-col gap-2 my-8">
        <div class="mb-2">
          <MaterialIcon size="2rem" color="fill-neutral-500">
            <Price />
          </MaterialIcon>
        </div>

        <h3 class="text-md text-neutral-500">No themes selected yet</h3>
        <p class="text-neutral-500 text-xs">
          Select themes from the AI-generated suggestions below
        </p>
      </div>
    {:else}
      <div class="mt-4">
        {#each $selectedThemesStore.data?.results as selectedTheme}
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
        disabled={!dataRequested || $selectedThemesStore.isLoading ||
          $selectedThemesStore.data?.results.length === 0}
        handleClick={() =>
          (isConfirmSignOffModalOpen = !isConfirmSignOffModalOpen)}
      >
        <div class="flex justify-center items-center gap-2 w-full">
          <MaterialIcon color="fill-white">
            <CheckCircle />
          </MaterialIcon>

          <span>
            {#if !dataRequested || $selectedThemesStore.isLoading}
              Loading Selected Themes
            {:else}
              Sign Off Selected Themes ({$selectedThemesStore.data?.results.length})
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
      confirmText={"Confirm Sign Off"}
      handleConfirm={confirmSignOff}
    >
      <p class="text-sm text-neutral-500">
        Are you sure you want to sign off on these {numSelectedThemesText(
          $selectedThemesStore.data?.results,
        )} for Question {$questionStore.data?.number}?
      </p>

      <h4 class="text-xs font-bold my-4">Selected themes:</h4>

      <div class="max-h-64 overflow-y-auto">
        {#each $selectedThemesStore.data?.results as selectedTheme}
          <Panel bg={true} border={false}>
            <h5 class="text-xs font-bold mb-1">{selectedTheme.name}</h5>
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
          <div class="flex items-center justify-between mb-2">
            <div class="flex items-center gap-2">
              <MaterialIcon color="fill-secondary">
                <SmartToy />
              </MaterialIcon>

              <h3>AI Generated Themes</h3>

              <Tag variant="success">
                {$generatedThemesStore.data?.results.length} available
              </Tag>
            </div>

            <div class="flex items-center gap-4">
              <div class="flex items-center gap-1 text-xs text-neutral-500">
                <MaterialIcon color="fill-neutral-500">
                  <Stacks />
                </MaterialIcon>
                Multi-level themes
              </div>
              <Button
                size="sm"
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
            </div>
          </div>

          <p class="text-neutral-500 text-sm">
            Browse AI-generated themes organised by topic hierarchy. Click
            "Select Theme" to add themes to your selected list for analysis.
          </p>
        </Panel>
      </div>

      {#each $generatedThemesStore.data?.results as theme}
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
