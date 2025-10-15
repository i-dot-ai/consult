<script lang="ts">
  import clsx from "clsx";

  import { fade, fly } from "svelte/transition";

  import type { GeneratedTheme } from "../../../global/types";

  import Panel from "../../dashboard/Panel/Panel.svelte";
  import Button from "../../inputs/Button/Button.svelte";
  import MaterialIcon from "../../MaterialIcon.svelte";
  import Delete from "../../svg/material/Delete.svelte";
  import Docs from "../../svg/material/Docs.svelte";
  import EditSquare from "../../svg/material/EditSquare.svelte";
  import AddCustomTheme from "../AddCustomTheme/AddCustomTheme.svelte";
  import AnswersList from "../AnswersList/AnswersList.svelte";

  export interface Props {
    theme: GeneratedTheme,
    answers: string[],
    removeTheme: (themeId: string) => void,
    updateTheme: (themeId: string, title: string, description: string) => void,
  }

  let {
    theme,
    answers = [],
    removeTheme = () => {},
    updateTheme = () => {},
  }: Props = $props();

  let showAnswers = $state(false);
  let editing = $state(false);
</script>

<article class="bg-white rounded-lg">
  {#if editing}
    <div in:fade>
      <AddCustomTheme
        variant="edit"
        handleCancel={() => (editing = false)}
        handleConfirm={(title, description) => {
          updateTheme(theme.id, title, description);
        }}
      />
    </div>
  {:else}
    <div in:fade>
      <Panel>
        <div class="grid grid-cols-12">
          <div class={clsx([showAnswers ? "col-span-4" : "col-span-12"])}>
            <header>
              <h2>{theme.name}</h2>
            </header>

            <p class="text-sm text-neutral-700 my-4">
              {theme.description}
            </p>

            <footer class="flex items-center flex-wrap gap-2">
              <Button size="sm" handleClick={() => (editing = !editing)}>
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

              <Button
                size="sm"
                handleClick={() => (showAnswers = !showAnswers)}
                disabled={!answers.length}
              >
                <MaterialIcon color="fill-neutral-500">
                  <Docs />
                </MaterialIcon>
                <span class="block w-full text-start">
                  Respresentative Responses
                </span>
              </Button>
            </footer>
          </div>

          {#if showAnswers}
            <aside
              in:fly={{ x: 300 }}
              class="col-span-8 border-l border-neutral-200 ml-4 pl-4"
            >
              <AnswersList title="Representative Responses" {answers} />
            </aside>
          {/if}
        </div>
      </Panel>
    </div>
  {/if}
</article>
