<script lang="ts">
  import clsx from "clsx";

  import { tick } from "svelte";
  import { fade, slide } from "svelte/transition";

  import { createQuery, createMutation } from "@tanstack/svelte-query";
  import { queryClient } from "../../global/queryClient";

  import {
    getApiConfirmSignOffUrl,
    getApiCreateSelectedThemeUrl,
    getApiDeleteSelectedThemeUrl,
    getApiGetGeneratedThemesUrl,
    getApiGetSelectedThemesUrl,
    getApiSelectGeneratedThemeUrl,
    getApiUpdateSelectedThemeUrl,
    getThemeSignOffUrl,
  } from "../../global/routes";

  import {
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
    question: Question;
  }

  let { consultationId, questionId, question }: Props = $props();

  const selectedThemesQuery = createQuery<SelectedThemesResponse>(
    () => ({
      queryKey: ["selectedThemes", consultationId, questionId],
      queryFn: async () => {
        const response = await fetch(
          getApiGetSelectedThemesUrl(consultationId, questionId),
        );
        if (!response.ok) throw new Error("Failed to fetch selected themes");
        return response.json();
      },
    }),
    () => queryClient,
  );

  const generatedThemesQuery = createQuery<GeneratedThemesResponse>(
    () => ({
      queryKey: ["generatedThemes", consultationId, questionId],
      queryFn: async () => {
        const response = await fetch(
          getApiGetGeneratedThemesUrl(consultationId, questionId),
        );
        if (!response.ok) throw new Error("Failed to fetch generated themes");
        return response.json();
      },
    }),
    () => queryClient,
  );

  const createThemeMutation = createMutation(
    () => ({
      mutationFn: async (newTheme: { name: string; description: string }) => {
        const response = await fetch(
          getApiCreateSelectedThemeUrl(consultationId, questionId),
          {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(newTheme),
          },
        );
        if (!response.ok) throw new Error("Failed to create theme");
        return response.json();
      },
      onSuccess: () => {
        queryClient.invalidateQueries({
          queryKey: ["selectedThemes", consultationId, questionId],
        });
      },
    }),
    () => queryClient,
  );

  const deleteThemeMutation = createMutation<
    void,
    {
      status: number;
      last_modified_by?: { email: string };
      latest_version?: string;
    },
    { themeId: string; version: number }
  >(
    () => ({
      mutationFn: async ({ themeId, version }) => {
        const response = await fetch(
          getApiDeleteSelectedThemeUrl(consultationId, questionId, themeId),
          {
            method: "DELETE",
            headers: {
              "Content-Type": "application/json",
              "If-Match": String(version),
            },
          },
        );
        if (!response.ok) {
          const errData = await response.json().catch(() => ({}));
          throw { status: response.status, ...errData };
        }
      },
      onSuccess: () => {
        queryClient.invalidateQueries({
          queryKey: ["selectedThemes", consultationId, questionId],
        });
        queryClient.invalidateQueries({
          queryKey: ["generatedThemes", consultationId, questionId],
        });
      },
      onError: (error) => {
        if (error.status === 404) {
          // Theme already deleted, just refetch
          queryClient.invalidateQueries({
            queryKey: ["selectedThemes", consultationId, questionId],
          });
          queryClient.invalidateQueries({
            queryKey: ["generatedThemes", consultationId, questionId],
          });
        } else if (error.status === 412) {
          errorData = {
            type: "remove-conflict",
            lastModifiedBy: error.last_modified_by?.email || "",
            latestVersion: error.latest_version || "",
          };
        } else {
          errorData = { type: "unexpected" };
          console.error(error);
        }
      },
    }),
    () => queryClient,
  );

  const updateThemeMutation = createMutation<
    unknown,
    {
      status: number;
      last_modified_by?: { email: string };
      latest_version?: string;
    },
    { themeId: string; version: number; name: string; description: string }
  >(
    () => ({
      mutationFn: async ({ themeId, version, name, description }) => {
        const response = await fetch(
          getApiUpdateSelectedThemeUrl(consultationId, questionId, themeId),
          {
            method: "PATCH",
            headers: {
              "Content-Type": "application/json",
              "If-Match": String(version),
            },
            body: JSON.stringify({ name, description }),
          },
        );
        if (!response.ok) {
          const errData = await response.json().catch(() => ({}));
          throw { status: response.status, ...errData };
        }
        return response.json();
      },
      onSuccess: () => {
        queryClient.invalidateQueries({
          queryKey: ["selectedThemes", consultationId, questionId],
        });
      },
      onError: (error) => {
        if (error.status === 404) {
          errorData = { type: "theme-does-not-exist" };
        } else if (error.status === 412) {
          errorData = {
            type: "edit-conflict",
            lastModifiedBy: error.last_modified_by?.email || "",
            latestVersion: error.latest_version || "",
          };
        } else {
          errorData = { type: "unexpected" };
        }
      },
    }),
    () => queryClient,
  );

  const selectGeneratedThemeMutation = createMutation(
    () => ({
      mutationFn: async (themeId: string) => {
        const response = await fetch(
          getApiSelectGeneratedThemeUrl(consultationId, questionId, themeId),
          { method: "POST" },
        );
        if (!response.ok) throw new Error("Failed to select theme");
        return response.json();
      },
      onSuccess: () => {
        queryClient.invalidateQueries({
          queryKey: ["selectedThemes", consultationId, questionId],
        });
        queryClient.invalidateQueries({
          queryKey: ["generatedThemes", consultationId, questionId],
        });
      },
    }),
    () => queryClient,
  );

  const confirmSignOffMutation = createMutation(
    () => ({
      mutationFn: async () => {
        const response = await fetch(
          getApiConfirmSignOffUrl(consultationId, questionId),
          {
            method: "PATCH",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ theme_status: "confirmed" }),
          },
        );
        if (!response.ok) throw new Error("Failed to confirm sign-off");
        return response.json();
      },
      onSuccess: () => {
        location.replace(getThemeSignOffUrl(consultationId));
      },
      onError: () => {
        isConfirmSignOffModalOpen = false;
        errorData = { type: "unexpected" };
      },
    }),
    () => queryClient,
  );

  let isConfirmSignOffModalOpen: boolean = $state(false);
  let addingCustomTheme: boolean = $state(false);
  let errorData: ErrorType | null = $state(null);
  let themesBeingSelected: string[] = $state([]);

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
    flattenGeneratedThemes(generatedThemesQuery.data?.results),
  );

  let expandedThemes: string[] = $derived(
    flatGeneratedThemes.map((theme) => theme.id),
  );

  let hasNestedThemes = $derived(
    generatedThemesQuery.data?.results?.some((theme: GeneratedTheme) =>
      Boolean(theme.children && theme.children.length > 0),
    ),
  );

  const errorModalOnClose = () => {
    queryClient.invalidateQueries({
      queryKey: ["selectedThemes", consultationId, questionId],
    });
    queryClient.invalidateQueries({
      queryKey: ["generatedThemes", consultationId, questionId],
    });
    errorData = null;
  };

  const createTheme = async (title: string, description: string) => {
    await createThemeMutation.mutateAsync({
      name: title,
      description: description,
    });
  };

  const removeTheme = (themeId: string) => {
    const selectedTheme = selectedThemesQuery.data?.results.find(
      (theme) => theme.id === themeId,
    );

    if (!selectedTheme) {
      console.error(`Selected theme ${themeId} not found`);
      return;
    }

    deleteThemeMutation.mutate({
      themeId,
      version: selectedTheme.version,
    });
  };

  const updateTheme = (themeId: string, title: string, description: string) => {
    const selectedTheme = selectedThemesQuery.data?.results.find(
      (theme) => theme.id === themeId,
    );

    if (!selectedTheme) {
      console.error(`Selected theme ${themeId} not found`);
      return;
    }

    updateThemeMutation.mutate({
      themeId,
      version: selectedTheme.version,
      name: title,
      description,
    });
  };

  const handleSelectGeneratedTheme = async (newTheme: GeneratedTheme) => {
    themesBeingSelected = [...themesBeingSelected, newTheme.id];

    try {
      const createdTheme = await selectGeneratedThemeMutation.mutateAsync(
        newTheme.id,
      );
      await queryClient.refetchQueries({
        queryKey: ["selectedThemes", consultationId, questionId],
      });

      await tick(); // Wait for the DOM to update before scrolling

      document
        .querySelector(`article[data-themeid="${createdTheme.id}"]`)
        ?.scrollIntoView();
    } finally {
      themesBeingSelected = themesBeingSelected.filter(
        (themeId) => themeId !== newTheme.id,
      );
    }
  };

  const confirmSignOff = () => {
    confirmSignOffMutation.mutate();
  };

  const numSelectedThemesText = (themes?: Array<SelectedTheme>): string => {
    if (!themes?.length) return "";
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
    >
      <span class="p-1"> Choose another question </span>
    </Button>
  </div>
</TitleRow>

<section class="my-8">
  <QuestionCard
    skeleton={false}
    {consultationId}
    {question}
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
              {selectedThemesQuery.data?.results.length ?? 0} selected
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
          {#if (selectedThemesQuery.data?.results.length ?? 0) > 0}
            Manage your {numSelectedThemesText(
              selectedThemesQuery.data?.results,
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
          initialTitle=""
          initialDescription=""
        />
      </div>
    {/if}

    {#if selectedThemesQuery.data?.results.length === 0}
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
    {:else if selectedThemesQuery.data?.results}
      <div class="mt-4">
        {#each selectedThemesQuery.data.results as selectedTheme (selectedTheme.id)}
          <div transition:slide={{ duration: 150 }} class="mb-4 last:mb-0">
            <SelectedThemeCard
              {consultationId}
              {questionId}
              theme={selectedTheme}
              {removeTheme}
              {updateTheme}
            />
          </div>
        {/each}
      </div>

      <hr class="my-4" />

      <Button
        variant="primary"
        fullWidth={true}
        disabled={selectedThemesQuery.isLoading ||
          selectedThemesQuery.data?.results.length === 0}
        handleClick={() =>
          (isConfirmSignOffModalOpen = !isConfirmSignOffModalOpen)}
      >
        <div class="flex w-full items-center justify-center gap-2">
          <MaterialIcon color="fill-white">
            <CheckCircle />
          </MaterialIcon>

          <span>
            {#if selectedThemesQuery.isLoading}
              Loading Selected Themes
            {:else}
              Sign Off Selected Themes ({selectedThemesQuery.data?.results
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
          selectedThemesQuery.data?.results,
        )} for Question {question.number}?
      </p>

      <h4 class="my-4 text-xs font-bold">Selected themes:</h4>

      <div class="max-h-64 overflow-y-auto">
        {#each selectedThemesQuery.data?.results ?? [] as selectedTheme (selectedTheme.id)}
          <Panel bg={true} border={false}>
            <h5 class="mb-1 text-xs font-bold">{selectedTheme.name}</h5>
            <p class="text-xs text-neutral-500">
              {selectedTheme.description}
            </p>
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
                  generatedThemesQuery.data?.results || [],
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

      {#each generatedThemesQuery.data?.results ?? [] as theme (theme.id)}
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
