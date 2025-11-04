<script lang="ts">
  import clsx from "clsx";

  import { fade, fly, slide } from "svelte/transition";

  import { createFetchStore } from "../../global/stores";
  import {
    getApiConfirmSignOffUrl,
    getApiCreateSelectedThemeUrl,
    getApiDeleteSelectedThemeUrl,
    getApiGetGeneratedThemesUrl,
    getApiGetSelectedThemesUrl,
    getApiQuestionsUrl,
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
  import AddCustomTheme from "../theme-sign-off/AddCustomTheme/AddCustomTheme.svelte";
  import SelectedThemeCard from "../theme-sign-off/SelectedThemeCard/SelectedThemeCard.svelte";
  import GeneratedThemeCard from "../theme-sign-off/GeneratedThemeCard/GeneratedThemeCard.svelte";
  import CheckCircle from "../svg/material/CheckCircle.svelte";
  import OnboardingTour from "../OnboardingTour/OnboardingTour.svelte";
  import SmartToy from "../svg/material/SmartToy.svelte";
  import Stacks from "../svg/material/Stacks.svelte";
  import Tag from "../Tag/Tag.svelte";
  import Modal from "../Modal/Modal.svelte";
  import Alert from "../Alert.svelte";
  import Warning from "../svg/material/Warning.svelte";

  let {
    consultationId = "",
    questionId = "",
    questionDataMock,
    generatedThemesMock,
    selectedThemesMock,
    removeThemeMock,
    createThemeMock,
    updateThemeMock,
    answersMock,
    selectGeneratedThemeMock,
  } = $props();

  let isConfirmSignOffModalOpen = $state(false);
  let isErrorModalOpen = $state(false);
  let addingCustomTheme = $state(false);
  let expandedThemes: string[] = $state([]);

  const {
    load: loadSelectedThemes,
    loading: isSelectedThemesLoading,
    data: selectedThemesData,
    error: selectedThemesError,
  } = createFetchStore(selectedThemesMock);

  const {
    load: loadGeneratedThemes,
    loading: isGeneratedThemesLoading,
    data: generatedThemesData,
    error: generatedThemesError,
  } = createFetchStore(generatedThemesMock);

  const {
    load: createSelectedTheme,
    loading: isCreatingSelectedTheme,
    data: createSelectedThemeData,
    error: createSelectedThemeError,
  } = createFetchStore(createThemeMock);

  const {
    load: loadConfirmSignOff,
    loading: isConfirmSignOffLoading,
    data: confirmSignOffData,
    error: confirmSignOffError,
  } = createFetchStore();

  const {
    load: loadRemoveTheme,
    loading: isRemoveThemeLoading,
    data: removeThemeData,
    error: removeThemeError,
  } = createFetchStore(removeThemeMock);

  const {
    load: updateSelectedTheme,
    loading: isUpdatingTheme,
    data: updateThemeData,
    error: updateThemeError,
  } = createFetchStore(updateThemeMock);

  const {
    load: selectGeneratedTheme,
    loading: isSelectingGeneratedTheme,
    data: selectGeneratedThemeData,
    error: selectGeneratedThemeError,
  } = createFetchStore(selectGeneratedThemeMock);

  const {
    load: loadQuestion,
    loading: isQuestionLoading,
    data: questionData,
    error: questionError,
  } = createFetchStore(questionDataMock);

  let flatGeneratedThemes = $derived(flattenArray($generatedThemesData?.results));

  $effect(() => {
    expandedThemes = flatGeneratedThemes.map(theme => theme.id);
  })

  $effect(() => {
    loadSelectedThemes(getApiGetSelectedThemesUrl(consultationId, questionId));
    loadGeneratedThemes(
      getApiGetGeneratedThemesUrl(consultationId, questionId),
    );
    loadQuestion(getApiQuestionUrl(consultationId, questionId));
  });

  const createTheme = async (title: string, description: string) => {
    await createSelectedTheme(
      getApiCreateSelectedThemeUrl(consultationId, questionId),
      "POST",
      {
        name: title,
        description: description,
      },
    );

    loadSelectedThemes(getApiGetSelectedThemesUrl(consultationId, questionId));
  };
  const removeTheme = async (themeId: string) => {
    const selectedTheme = $selectedThemesData?.results.find(
      (theme) => theme.id === themeId,
    );

    await loadRemoveTheme(
      getApiDeleteSelectedThemeUrl(consultationId, questionId, themeId),
      "DELETE",
      undefined,
      {
        "If-Match": selectedTheme.version,
      },
    );

    loadSelectedThemes(getApiGetSelectedThemesUrl(consultationId, questionId));
    loadGeneratedThemes(
      getApiGetGeneratedThemesUrl(consultationId, questionId),
    );
  };
  const updateTheme = async (
    themeId: string,
    title: string,
    description: string,
  ) => {
    const selectedTheme = $selectedThemesData?.results.find(
      (theme) => theme.id === themeId,
    );

    await updateSelectedTheme(
      getApiUpdateSelectedThemeUrl(consultationId, questionId, themeId),
      "PATCH",
      {
        name: title,
        description: description,
      },
      {
        "If-Match": selectedTheme.version,
      },
    );

    loadSelectedThemes(getApiGetSelectedThemesUrl(consultationId, questionId));
  };

  const handleSelectGeneratedTheme = async (newTheme) => {
    await selectGeneratedTheme(
      getApiSelectGeneratedThemeUrl(consultationId, questionId, newTheme.id),
      "POST",
    );

    loadSelectedThemes(getApiGetSelectedThemesUrl(consultationId, questionId));
    loadGeneratedThemes(
      getApiGetGeneratedThemesUrl(consultationId, questionId),
    );
  };

  const confirmSignOff = async () => {
    await loadConfirmSignOff(
      getApiConfirmSignOffUrl(consultationId, questionId),
      "PATCH",
      {
        theme_status: "confirmed",
      },
    );

    if ($confirmSignOffError) {
      isConfirmSignOffModalOpen = false;
      isErrorModalOpen = true;
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
  }
  const isAllThemesExpanded = (): boolean => {
    return expandedThemes.length === flatGeneratedThemes.length
  };
  const expandAllThemes = () => {
    expandedThemes = flatGeneratedThemes.map(theme => theme.id);
  }
  const collapseAllThemes = () => {
    expandedThemes = [];
  }
  const expandTheme = (themeId: string) => {
    expandedThemes = [...expandedThemes, themeId];
  }
  const collapseTheme = (themeId: string) => {
    expandedThemes = expandedThemes.filter(theme => theme !== themeId);
  }
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

<svelte:boundary>
  <section
    class={clsx([
      "selected-section",
      "my-4",
      "p-4",
      "bg-pink-50/25",
      "rounded-xl",
      "border",
      "border-pink-50",
    ])}
  >
    <div id="onboarding-step-2" class="mb-4">
      <Panel variant="primary" bg={true} border={true}>
        <div class="flex items-center justify-between mb-2">
          <div class="flex items-center gap-2">
            <MaterialIcon color={"fill-primary"}>
              <CheckCircle />
            </MaterialIcon>

            <h3>Selected Themes</h3>
          </div>

          <Button
            size="sm"
            handleClick={() => (addingCustomTheme = !addingCustomTheme)}
            highlighted={addingCustomTheme}
            highlightVariant="primary"
          >
            <span
              class={clsx([
                "flex items-center justify-between text-primary",
                addingCustomTheme && "text-white",
              ])}>+ Add Custom Theme</span
            >
          </Button>
        </div>

        <p class="text-neutral-500 text-sm">
          Manage your {numSelectedThemesText($selectedThemesData?.results)} for the
          AI in mapping responses. Edit titles and descriptions, or add new themes
          as needed.
        </p>
      </Panel>
    </div>

    {#if addingCustomTheme}
      <div transition:slide>
        <AddCustomTheme
          handleConfirm={async (title: string, description: string) => {
            await createTheme(title, description);
            addingCustomTheme = false;
          }}
          handleCancel={() => (addingCustomTheme = false)}
        />
      </div>
    {/if}

    {#if $selectedThemesData?.results.length === 0}
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
        {#each $selectedThemesData?.results as selectedTheme}
          <div transition:slide={{ duration: 150 }} class="mb-4 last:mb-0">
            <SelectedThemeCard
              {consultationId}
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
        disabled={$isSelectedThemesLoading ||
          $selectedThemesData?.results.length === 0}
        handleClick={() => (isConfirmSignOffModalOpen = !isConfirmSignOffModalOpen)}
      >
        <div
          id="onboarding-step-3"
          class="flex justify-center items-center gap-2 w-full"
        >
          <MaterialIcon color="fill-white">
            <CheckCircle />
          </MaterialIcon>

          <span>
            {#if $isSelectedThemesLoading}
              Loading Selected Themes
            {:else}
              Sign Off Selected Themes ({$selectedThemesData?.results.length})
            {/if}
          </span>
        </div>
      </Button>
    {/if}

    <Modal
      open={isConfirmSignOffModalOpen}
      setOpen={(newOpen: boolean) => (isConfirmSignOffModalOpen = newOpen)}
      confirmText={"Confirm Sign Off"}
      handleConfirm={confirmSignOff}
    >
      <div class="flex items-center gap-2 mb-2">
        <MaterialIcon color="fill-primary">
          <CheckCircle />
        </MaterialIcon>
        <h3 class="font-bold">Confirm Theme Sign Off</h3>
      </div>

      <p class="text-sm text-neutral-500">
        Are you sure you want to sign off on these {numSelectedThemesText(
          $selectedThemesData?.results,
        )} for Question {$questionData?.number}?
      </p>

      <h4 class="text-xs font-bold my-4">Selected themes:</h4>

      <div class="max-h-64 overflow-y-auto">
        {#each $selectedThemesData?.results as selectedTheme}
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
  <p class={clsx(["m-auto", "w-max", "bg-white", "px-4"])}>
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
              <MaterialIcon color="fill-emerald-700">
                <SmartToy />
              </MaterialIcon>

              <h3>AI Generated Themes</h3>

              <Tag variant="success">
                {$generatedThemesData?.results.length} available
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
                    "flex items-center justify-between gap-1 text-emerald-700",
                    addingCustomTheme && "text-white",
                  ])}
                >
                  <MaterialIcon color="fill-emerald-700">
                    <Stacks />
                  </MaterialIcon>
                  {isAllThemesExpanded()
                    ? "Collapse All"
                    : "Expand All"}
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

      {#each $generatedThemesData?.results as theme}
        <GeneratedThemeCard
          {consultationId}
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
        />
      {/each}
    </Panel>
  </section>

  {#snippet failed(error)}
    <div>
      {console.error(error)}

      <Panel>
        <Alert>Unexpected generated themes error</Alert>
      </Panel>
    </div>
  {/snippet}
</svelte:boundary>

<Modal
  open={isErrorModalOpen}
  setOpen={(newOpen: boolean) => (isErrorModalOpen = newOpen)}
  confirmText={"Ok"}
  handleConfirm={() => isErrorModalOpen = false}
>
  <div class="flex items-center gap-2 mb-2">
    <MaterialIcon color="fill-orange-600" size="1.3rem">
      <Warning />
    </MaterialIcon>

    <h3 class="text-orange-600 text-lg">Theme Update Failed</h3>
  </div>

  <p>Theme failed to update due to error: {$confirmSignOffError}</p>
</Modal>

<OnboardingTour
  key="theme-sign-off"
  steps={[
    {
      id: "onboarding-step-1",
      title: "Select Themes",
      body: `Browse the AI-generated themes and click "Select Theme" to move them to your selected themes list. You can view example responses for each theme to understand what types of consultation responses it represents.`,
    },
    {
      id: "onboarding-step-2",
      title: "Edit & Manage",
      body: "Once themes are selected, you can edit their titles and descriptions by clicking the edit button, or add completely new themes to better organize your analysis.",
    },
    {
      id: "onboarding-step-3",
      title: "Sign Off & Proceed",
      body: `When you're satisfied with your theme selection and edits, click "Sign Off Selected Themes" to proceed with mapping consultation responses against your finalised themes.`,
    },
  ]}
/>

<style>
  .selected-section :global(div[data-testid="panel-component"]) {
    margin: 0;
  }
</style>

