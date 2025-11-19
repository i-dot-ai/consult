<script lang="ts">
  import clsx from "clsx";

  import { fade, fly } from "svelte/transition";

  import type { GeneratedTheme } from "../../../global/types";
  import { createFetchStore } from "../../../global/stores";
  import { getApiAnswersUrl } from "../../../global/routes";

  import Panel from "../../dashboard/Panel/Panel.svelte";
  import Button from "../../inputs/Button/Button.svelte";
  import MaterialIcon from "../../MaterialIcon.svelte";
  import Delete from "../../svg/material/Delete.svelte";
  import Docs from "../../svg/material/Docs.svelte";
  import EditSquare from "../../svg/material/EditSquare.svelte";
  import ThemeForm from "../ThemeForm/ThemeForm.svelte";
  import AnswersList from "../AnswersList/AnswersList.svelte";
  import Tag from "../../Tag/Tag.svelte";

  export interface Props {
    consultationId: string;
    questionId: string;
    theme: GeneratedTheme;
    removeTheme: (themeId: string) => void;
    updateTheme: (themeId: string, title: string, description: string) => void;
    maxAnswers?: number;
    answersMock?: Function;
  }

  let {
    consultationId,
    questionId,
    theme,
    removeTheme = () => {},
    updateTheme = () => {},
    maxAnswers = 10,
    answersMock,
  }: Props = $props();

  const answersStore = createFetchStore(answersMock);

  let showAnswers = $state(false);
  let editing = $state(false);
  let answersRequested = $state(false);

  const resetAnswers = () => {
    $answersStore.data = null;
    showAnswers = false;
    answersRequested = false;
  }
</script>

<article class="bg-white rounded-lg" data-themeid={theme.id}>
  {#if editing}
    <div in:fade>
      <ThemeForm
        variant="edit"
        initialTitle={theme.name}
        initialDescription={theme.description}
        handleCancel={() => (editing = false)}
        handleConfirm={(title, description) => {
          updateTheme(theme.id, title, description);
          resetAnswers();
          editing = false;
        }}
      />
    </div>
  {:else}
    <div in:fade>
      <Panel>
        <div class="flex flex-wrap sm:flex-nowrap">
          <div class={clsx([showAnswers ? "md:w-1/3" : "md:w-auto"])}>
            <header class="flex items-center gap-2">
              <h2>{theme.name}</h2>

              {#if theme?.version > 1}
                <Tag variant="primary-light">Edited</Tag>
              {/if}
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
                  if (!$answersStore.data) {
                    const queryString = new URLSearchParams({
                      searchMode: "representative",
                      searchValue: `${theme.name} ${theme.description}`,
                      question_id: questionId
                    }).toString();

                    $answersStore.fetch(
                      `${getApiAnswersUrl(consultationId)}?${queryString}`,
                    );
                  }
                  showAnswers = !showAnswers;
                  answersRequested = true;
                }}
                disabled={$answersStore.isLoading && answersRequested}
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
                loading={$answersStore.isLoading}
                answers={$answersStore.data?.all_respondents
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
