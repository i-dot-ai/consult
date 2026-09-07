<script lang="ts">
  import clsx from "clsx";

  import { fade } from "svelte/transition";

  import type { ResponsesBody, SelectedTheme } from "../../../global/types";
  import { type MockFetch } from "../../../global/stores";
  import {
    formatTimeDeltaText,
    getTimeDeltaInMinutes,
  } from "../../../global/utils";

  import Panel from "../../dashboard/Panel/Panel.svelte";
  import Button from "../../inputs/Button/Button.svelte";
  import MaterialIcon from "../../MaterialIcon.svelte";
  import Delete from "../../svg/material/Delete.svelte";
  import EditSquare from "../../svg/material/EditSquare.svelte";
  import ThemeForm from "../ThemeForm/ThemeForm.svelte";
  import Tag from "../../Tag/Tag.svelte";

  export interface Props {
    consultationId: string;
    questionId: string;
    theme: SelectedTheme;
    removeTheme: (themeId: string) => void;
    updateTheme: (themeId: string, title: string, description: string) => void;
    maxResponses?: number;
    responsesMock?: MockFetch<ResponsesBody>;
  }

  let {
    theme,
    removeTheme = () => {},
    updateTheme = () => {},
  }: Props = $props();

  let editing = $state(false);
</script>

<article
  class="rounded-lg bg-white"
  data-testid="selected-theme-card"
  data-themeid={theme.id}
>
  {#if editing}
    <div in:fade>
      <ThemeForm
        variant="edit"
        initialTitle={theme.name}
        initialDescription={theme.description}
        handleCancel={() => (editing = false)}
        handleConfirm={(title, description) => {
          updateTheme(theme.id, title, description);
          editing = false;
        }}
      />
    </div>
  {:else}
    <div in:fade>
      <Panel>
        <div class="flex flex-wrap sm:flex-nowrap">
          <div class={clsx(["md:w-auto"])}>
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
                handleClick={() => (editing = !editing)}
                testId="selected-theme-edit-button"
              >
                <MaterialIcon color="fill-neutral-500">
                  <EditSquare />
                </MaterialIcon>
                Edit
              </Button>

              <Button size="sm" handleClick={() => removeTheme(theme.id)}>
                <MaterialIcon color="fill-neutral-500">
                  <Delete />
                </MaterialIcon>
                Remove
              </Button>
            </footer>
          </div>
        </div>
      </Panel>
    </div>
  {/if}
</article>
