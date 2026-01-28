<script lang="ts">
  import clsx from "clsx";

  import { fade, slide } from "svelte/transition";

  import { createQuery, createMutation } from "@tanstack/svelte-query";
  import { queryClient } from "../../../../global/queryClient";
  import {
    getApiConfirmSignOffUrl,
    getApiGetSelectedThemesUrl,
    getThemeSignOffUrl,
  } from "../../../../global/routes";
  import type {
    Question,
    SelectedTheme,
    SelectedThemesResponse,
  } from "../../../../global/types";

  import Panel from "../../../dashboard/Panel/Panel.svelte";
  import Button from "../../../inputs/Button/Button.svelte";
  import MaterialIcon from "../../../MaterialIcon.svelte";
  import CheckCircle from "../../../svg/material/CheckCircle.svelte";
  import Price from "../../../svg/material/Price.svelte";
  import Tag from "../../../Tag/Tag.svelte";
  import Modal from "../../../Modal/Modal.svelte";
  import Alert from "../../../Alert.svelte";

  import AddTheme from "./AddTheme/AddTheme.svelte";
  import SelectedThemeCard from "./SelectedThemeCard/SelectedThemeCard.svelte";
  import ErrorSavingTheme, {
    type SaveThemeError,
  } from "./ErrorSavingTheme/ErrorSavingTheme.svelte";

  interface Props {
    consultationId: string;
    questionId: string;
    question: Question;
  }

  let { consultationId, questionId, question }: Props = $props();

  let errorData: SaveThemeError | null = $state(null);

  const showError = (error: SaveThemeError) => {
    errorData = error;
  };

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

  const numSelectedThemesText = (themes?: Array<SelectedTheme>): string => {
    if (!themes?.length) return "";
    return `${themes.length} selected theme${themes.length > 1 ? "s" : ""}`;
  };

  const confirmSignOff = () => {
    confirmSignOffMutation.mutate();
  };
</script>

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
      <AddTheme
        {consultationId}
        {questionId}
        {showError}
        onSuccess={() => (addingCustomTheme = false)}
        onCancel={() => (addingCustomTheme = false)}
      />
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
              {showError}
              theme={selectedTheme}
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
      confirmButtonDisabled={confirmSignOffMutation.isPending}
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

    {#if errorData}
      <ErrorSavingTheme {...errorData} onClose={() => (errorData = null)} />
    {/if}
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

<style>
  .selected-section :global(div[data-testid="panel-component"]) {
    margin: 0;
  }
</style>
