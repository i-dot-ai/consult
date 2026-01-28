<script lang="ts">
  import { fade } from "svelte/transition";

  import { createMutation } from "@tanstack/svelte-query";
  import { queryClient } from "../../../../../global/queryClient";
  import { getApiUpdateSelectedThemeUrl } from "../../../../../global/routes";
  import type { SelectedTheme } from "../../../../../global/types";

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
    unknown,
    {
      status: number;
      last_modified_by?: { email: string };
      latest_version?: string;
    },
    { name: string; description: string }
  >(
    () => ({
      mutationFn: async ({ name, description }) => {
        const response = await fetch(
          getApiUpdateSelectedThemeUrl(consultationId, questionId, theme.id),
          {
            method: "PATCH",
            headers: {
              "Content-Type": "application/json",
              "If-Match": String(theme.version),
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
