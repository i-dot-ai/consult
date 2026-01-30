<script lang="ts">
  import clsx from "clsx";

  import { fade, fly } from "svelte/transition";

  import { createMutation } from "@tanstack/svelte-query";
  import { queryClient } from "../../../../../global/queryClient";
  import {
    selectedThemes,
    deleteSelectedTheme,
    type SelectedTheme,
    type SelectedThemeMutationError,
  } from "../../../../../global/queries/selectedThemes";
  import { candidateThemes } from "../../../../../global/queries/candidateThemes";
  import {
    formatTimeDeltaText,
    getTimeDeltaInMinutes,
  } from "../../../../../global/utils";

  import Panel from "../../../../dashboard/Panel/Panel.svelte";
  import Button from "../../../../inputs/Button/Button.svelte";
  import MaterialIcon from "../../../../MaterialIcon.svelte";
  import Delete from "../../../../svg/material/Delete.svelte";
  import Docs from "../../../../svg/material/Docs.svelte";
  import EditSquare from "../../../../svg/material/EditSquare.svelte";
  import EditTheme from "../EditTheme/EditTheme.svelte";
  import RepresentativeResponses from "../../RepresentativeResponses/RepresentativeResponses.svelte";
  import Tag from "../../../../Tag/Tag.svelte";
  import type { SaveThemeError } from "../ErrorSavingTheme/ErrorSavingTheme.svelte";

  interface Props {
    consultationId: string;
    questionId: string;
    showError: (error: SaveThemeError) => void;
    theme: SelectedTheme;
  }

  let { consultationId, questionId, showError, theme }: Props = $props();

  let showRepresentativeResponses = $state(false);
  let editing = $state(false);

  const deleteThemeMutation = createMutation<
    void,
    SelectedThemeMutationError,
    void
  >(
    () => ({
      mutationFn: () =>
        deleteSelectedTheme(
          consultationId,
          questionId,
          theme.id,
          theme.version,
        ),
      onSuccess: () => {
        queryClient.invalidateQueries({
          queryKey: selectedThemes.list.key(consultationId, questionId),
        });
        queryClient.invalidateQueries({
          queryKey: candidateThemes.list.key(consultationId, questionId),
        });
      },
      onError: (error) => {
        if (error.status === 404) {
          // SelectedTheme has already been deleted, just refetch
          queryClient.invalidateQueries({
            queryKey: selectedThemes.list.key(consultationId, questionId),
          });
          queryClient.invalidateQueries({
            queryKey: candidateThemes.list.key(consultationId, questionId),
          });
        } else if (error.status === 412) {
          showError({
            type: "remove-conflict",
            lastModifiedBy: error.last_modified_by?.email || "",
            latestVersion: error.latest_version || "",
          });
        } else {
          showError({ type: "unexpected" });
          console.error(error);
        }
      },
    }),
    () => queryClient,
  );

  const handleEditSuccess = () => {
    // Invalidate representative responses cache when theme is edited since search terms changed
    queryClient.invalidateQueries({
      queryKey: [
        "representativeResponses",
        consultationId,
        questionId,
        "selected",
        theme.id,
      ],
    });
    showRepresentativeResponses = false;
    editing = false;
  };
</script>

<article class="rounded-lg bg-white" data-themeid={theme.id}>
  {#if editing}
    <EditTheme
      {consultationId}
      {questionId}
      {showError}
      {theme}
      onSuccess={handleEditSuccess}
      onCancel={() => (editing = false)}
    />
  {:else}
    <div in:fade>
      <Panel>
        <div class="flex flex-wrap sm:flex-nowrap">
          <div
            class={clsx([
              showRepresentativeResponses ? "md:w-1/3" : "md:w-auto",
            ])}
          >
            <header class="flex items-center gap-2">
              <h2>{theme.name}</h2>

              {#if theme?.version > 1}
                <Tag variant="primary-light">Edited</Tag>
              {/if}
            </header>

            <p class="my-4 text-sm text-neutral-700">
              {theme.description}
            </p>

            <hr class="mb-4" />

            <small class="mb-4 block text-xs text-neutral-500">
              {theme.version > 1 ? "Edited" : "Added"}
              {formatTimeDeltaText(
                getTimeDeltaInMinutes(new Date(), new Date(theme.modified_at)),
              )} ago by {theme.last_modified_by}
            </small>

            <footer class="flex flex-wrap items-center gap-2">
              <Button
                size="sm"
                disabled={deleteThemeMutation.isPending}
                handleClick={() => (editing = !editing)}
              >
                <MaterialIcon color="fill-neutral-500">
                  <EditSquare />
                </MaterialIcon>
                Edit
              </Button>

              <Button
                size="sm"
                handleClick={() => deleteThemeMutation.mutate()}
                disabled={deleteThemeMutation.isPending}
              >
                <MaterialIcon color="fill-neutral-500">
                  <Delete />
                </MaterialIcon>
                Remove
              </Button>

              <Button
                size="sm"
                handleClick={() =>
                  (showRepresentativeResponses = !showRepresentativeResponses)}
                disabled={deleteThemeMutation.isPending}
              >
                <MaterialIcon color="fill-neutral-500">
                  <Docs />
                </MaterialIcon>
                <span class="block w-full text-start">
                  Representative Responses
                </span>
              </Button>
            </footer>
          </div>

          {#if showRepresentativeResponses}
            <aside
              transition:fly={{ x: 300 }}
              class="grow pt-4 sm:ml-4 sm:w-2/3 sm:border-l sm:border-neutral-200 sm:pl-4 sm:pt-0"
            >
              <RepresentativeResponses
                {consultationId}
                {questionId}
                themeName={theme.name}
                themeDescription={theme.description}
                themeId={theme.id}
                variant="selected"
              />
            </aside>
          {/if}
        </div>
      </Panel>
    </div>
  {/if}
</article>
