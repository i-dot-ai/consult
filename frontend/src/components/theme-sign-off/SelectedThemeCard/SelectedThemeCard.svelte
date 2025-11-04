<script lang="ts">
  import clsx from "clsx";

  import { fade, fly } from "svelte/transition";

  import type { GeneratedTheme } from "../../../global/types";
  import { createFetchStore } from "../../../global/stores";

  import Panel from "../../dashboard/Panel/Panel.svelte";
  import Button from "../../inputs/Button/Button.svelte";
  import MaterialIcon from "../../MaterialIcon.svelte";
  import Delete from "../../svg/material/Delete.svelte";
  import Docs from "../../svg/material/Docs.svelte";
  import EditSquare from "../../svg/material/EditSquare.svelte";
  import AddCustomTheme from "../AddCustomTheme/AddCustomTheme.svelte";
  import AnswersList from "../AnswersList/AnswersList.svelte";

  export interface Props {
    consultationId: string;
    theme: GeneratedTheme;
    removeTheme: (themeId: string) => void;
    updateTheme: (themeId: string, title: string, description: string) => void;
    maxAnswers?: number;
    answersMock?: Function;
  }

  let {
    consultationId,
    theme,
    removeTheme = () => {},
    updateTheme = () => {},
    maxAnswers = 10,
    answersMock,
  }: Props = $props();

  let {
    load: loadAnswers,
    loading: isAnswersLoading,
    data: answersData,
    error: answersError,
  } = createFetchStore(answersMock);

  let showAnswers = $state(false);
  let editing = $state(false);
  let answersRequested = $state(false);
</script>

<article class="bg-white rounded-lg">
  {#if editing}
    <div in:fade>
      <AddCustomTheme
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
          <div class={clsx([showAnswers ? "md:w-1/3" : "md:w-auto"])}>
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
                handleClick={() => {
                  if (!$answersData) {
                    loadAnswers(`
                      /api/consultations/${consultationId}/responses/?searchValue=${theme.name}&searchMode=semantic
                    `);
                  }
                  showAnswers = !showAnswers;
                  answersRequested = true;
                }}
                disabled={$isAnswersLoading && answersRequested}
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

          {#if showAnswers}
            <aside
              transition:fly={{ x: 300 }}
              class="grow sm:border-l sm:border-neutral-200 sm:ml-4 sm:pl-4 pt-4 sm:pt-0"
            >
              <AnswersList
                title="Representative Responses"
                loading={$isAnswersLoading}
                answers={$answersData?.all_respondents
                  .slice(0, maxAnswers)
                  .map((answer) => answer.free_text_answer_text) || []}
              />
            </aside>
          {/if}
        </div>
      </Panel>
    </div>
  {/if}
</article>
