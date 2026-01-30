<script lang="ts">
  import { fade } from "svelte/transition";

  import { createMutation } from "@tanstack/svelte-query";
  import { queryClient } from "../../../../../global/queryClient";
  import {
    selectedThemes,
    updateSelectedTheme,
    type SelectedTheme,
    type UpdateSelectedThemeBody,
    type SelectedThemeMutationError,
  } from "../../../../../global/queries/selectedThemes";

  import ThemeForm from "../ThemeForm/ThemeForm.svelte";
  import type { SaveThemeError } from "../ErrorSavingTheme/ErrorSavingTheme.svelte";

  interface Props {
    consultationId: string;
    questionId: string;
    showError: (error: SaveThemeError) => void;
    theme: SelectedTheme;
    onSuccess?: () => void;
    onCancel: () => void;
  }

  let {
    consultationId,
    questionId,
    showError,
    theme,
    onSuccess,
    onCancel,
  }: Props = $props();

  const updateThemeMutation = createMutation<
    SelectedTheme,
    SelectedThemeMutationError,
    UpdateSelectedThemeBody
  >(
    () => ({
      mutationFn: (body: UpdateSelectedThemeBody) =>
        updateSelectedTheme(
          consultationId,
          questionId,
          theme.id,
          theme.version,
          body,
        ),
      onSuccess: () => {
        queryClient.invalidateQueries({
          queryKey: selectedThemes.list.key(consultationId, questionId),
        });
        onSuccess?.();
      },
      onError: (error) => {
        if (error.status === 404) {
          showError({ type: "theme-does-not-exist" });
        } else if (error.status === 412) {
          showError({
            type: "edit-conflict",
            lastModifiedBy: error.last_modified_by?.email || "",
            latestVersion: error.latest_version || "",
          });
        } else {
          showError({ type: "unexpected" });
        }
        onCancel();
      },
    }),
    () => queryClient,
  );

  const handleConfirm = (title: string, description: string) => {
    updateThemeMutation.mutate({
      name: title,
      description,
    });
  };
</script>

<div in:fade>
  <ThemeForm
    variant="edit"
    {theme}
    {handleConfirm}
    handleCancel={onCancel}
    loading={updateThemeMutation.isPending}
  />
</div>
