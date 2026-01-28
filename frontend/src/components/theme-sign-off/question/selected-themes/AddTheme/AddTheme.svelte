<script lang="ts">
  import { slide } from "svelte/transition";

  import { createMutation } from "@tanstack/svelte-query";
  import { queryClient } from "../../../../../global/queryClient";
  import { getApiCreateSelectedThemeUrl } from "../../../../../global/routes";

  import ThemeForm from "../ThemeForm/ThemeForm.svelte";
  import type { SaveThemeError } from "../ErrorSavingTheme/ErrorSavingTheme.svelte";

  interface Props {
    consultationId: string;
    questionId: string;
    showError: (error: SaveThemeError) => void;
    onSuccess?: () => void;
    onCancel: () => void;
  }

  let { consultationId, questionId, showError, onSuccess, onCancel }: Props =
    $props();

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
        onSuccess?.();
      },
      onError: () => {
        showError({ type: "unexpected" });
      },
    }),
    () => queryClient,
  );

  const handleConfirm = async (title: string, description: string) => {
    await createThemeMutation.mutateAsync({
      name: title,
      description: description,
    });
  };
</script>

<div transition:slide>
  <ThemeForm
    variant="add"
    {handleConfirm}
    handleCancel={onCancel}
    loading={createThemeMutation.isPending}
  />
</div>
