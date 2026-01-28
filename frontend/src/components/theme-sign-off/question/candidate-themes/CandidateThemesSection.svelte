<script lang="ts">
  import clsx from "clsx";

  import { tick } from "svelte";

  import { createQuery, createMutation } from "@tanstack/svelte-query";
  import { queryClient } from "../../../../global/queryClient";
  import {
    getApiGetGeneratedThemesUrl,
    getApiSelectGeneratedThemeUrl,
  } from "../../../../global/routes";
  import type {
    GeneratedTheme,
    GeneratedThemesResponse,
  } from "../../../../global/types";

  import Panel from "../../../dashboard/Panel/Panel.svelte";
  import Button from "../../../inputs/Button/Button.svelte";
  import MaterialIcon from "../../../MaterialIcon.svelte";
  import SmartToy from "../../../svg/material/SmartToy.svelte";
  import Stacks from "../../../svg/material/Stacks.svelte";
  import Tag from "../../../Tag/Tag.svelte";
  import Alert from "../../../Alert.svelte";

  import CandidateThemeCard from "./CandidateThemeCard/CandidateThemeCard.svelte";

  interface Props {
    consultationId: string;
    questionId: string;
  }

  let { consultationId, questionId }: Props = $props();

  const candidateThemesQuery = createQuery<GeneratedThemesResponse>(
    () => ({
      queryKey: ["candidateThemes", consultationId, questionId],
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

  const selectCandidateThemeMutation = createMutation(
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
          queryKey: ["candidateThemes", consultationId, questionId],
        });
      },
    }),
    () => queryClient,
  );

  let themesBeingSelected: string[] = $state([]);

  let themes = $derived(candidateThemesQuery.data?.results ?? []);

  let collapsedThemes: string[] = $state([]);

  let isAllExpanded = $derived(collapsedThemes.length === 0);

  let hasMultiLevelThemes = $derived(themes.some((t) => t.children?.length));

  const toggleTheme = (themeId: string) => {
    if (collapsedThemes.includes(themeId)) {
      collapsedThemes = collapsedThemes.filter((id) => id !== themeId);
    } else {
      collapsedThemes = [...collapsedThemes, themeId];
    }
  };

  const toggleAllThemes = () => {
    if (isAllExpanded) {
      // Collapse all - collect IDs of themes with children
      const ids: string[] = [];
      const collectIds = (items: GeneratedTheme[]) => {
        for (const t of items) {
          if (t.children?.length) {
            ids.push(t.id);
            collectIds(t.children);
          }
        }
      };
      collectIds(themes);
      collapsedThemes = ids;
    } else {
      collapsedThemes = [];
    }
  };

  const handleSelectCandidateTheme = async (newTheme: GeneratedTheme) => {
    themesBeingSelected = [...themesBeingSelected, newTheme.id];

    try {
      const createdTheme = await selectCandidateThemeMutation.mutateAsync(
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
</script>

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
                {candidateThemesQuery.data?.results?.length ?? 0} available
              </Tag>
            </div>

            <div class="flex items-center gap-4">
              {#if hasMultiLevelThemes}
                <div class="flex items-center gap-1 text-xs text-neutral-500">
                  <MaterialIcon color="fill-neutral-500">
                    <Stacks />
                  </MaterialIcon>
                  Multi-level themes
                </div>

                <Button size="sm" handleClick={toggleAllThemes}>
                  <span
                    class={clsx([
                      "flex items-center justify-between gap-1 text-secondary",
                    ])}
                  >
                    <MaterialIcon color="fill-secondary">
                      <Stacks />
                    </MaterialIcon>
                    {isAllExpanded ? "Collapse All" : "Expand All"}
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

      {#each themes as theme (theme.id)}
        <CandidateThemeCard
          {consultationId}
          {questionId}
          {theme}
          {collapsedThemes}
          {toggleTheme}
          handleSelect={handleSelectCandidateTheme}
          {themesBeingSelected}
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
