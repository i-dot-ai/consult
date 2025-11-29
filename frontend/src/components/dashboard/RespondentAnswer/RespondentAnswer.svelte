<script lang="ts">
  import clsx from "clsx";

  import { fly } from "svelte/transition";

  import Panel from "../../dashboard/Panel/Panel.svelte";
  import Tag from "../../Tag/Tag.svelte";
  import MaterialIcon from "../../MaterialIcon.svelte";
  import Diamond from "../../svg/material/Diamond.svelte";
  import { getQuestionDetailUrl } from "../../../global/routes";

  export interface Props {
    consultationId: string;
    questionId: string;
    questionTitle: string;
    questionNumber: number;
    answerText: string;
    multiChoice: string[];
    themes: string[];
    evidenceRich: boolean;
    delay?: number;
  }

  let {
    consultationId = "",
    questionId = "",
    questionTitle = "",
    questionNumber = 0,
    answerText = "",
    multiChoice = [],
    themes = [],
    evidenceRich = false,
    delay = 0,
  }: Props = $props();
</script>

<div transition:fly={{ x: 300, delay: delay }}>
  <Panel border={true} bg={true}>
    <article>
      <header
        class="flex flex-col-reverse md:flex-row gap-y-4 justify-between items-start gap-2 mb-4"
      >
        <a href={getQuestionDetailUrl(consultationId, questionId)}>
          <div class="flex items-start gap-2">
            <div
              class={clsx([
                "question-number",
                "p-1",
                "rounded-lg",
                "border",
                "border-neutral-200",
                "text-xs",
                "bg-neutral-100",
                "transition-colors",
              ])}
            >
              Q{questionNumber}
            </div>

            <h3
              class={clsx([
                "text-xs",
                "text-neutral-500",
                "transition-colors",
                "mt-0.5",
              ])}
            >
              {questionTitle}
            </h3>
          </div>
        </a>

        <div class="whitespace-nowrap">
          {#if evidenceRich}
            <Tag variant="warning">
              <MaterialIcon size="0.9rem" color="fill-yellow-600">
                <Diamond />
              </MaterialIcon>

              <span class="text-xs">Evidence-rich</span>
            </Tag>
          {/if}
        </div>
      </header>

      {#if multiChoice?.length > 0}
        <div>
          <h4 class="mt-4 mb-1 uppercase text-xs text-neutral-500">
            Multiple Choice Response:
          </h4>

          <ul class="flex items-center flex-wrap gap-1">
            {#each multiChoice as multiChoiceAnswer (multiChoiceAnswer)}
              <li class="text-xs">
                {multiChoiceAnswer}
              </li>
            {/each}
          </ul>
        </div>
      {/if}

      <div>
        {#if multiChoice?.length > 0}
          <h4 class="mt-4 mb-1 uppercase text-xs text-neutral-500">
            Additional Comments:
          </h4>
        {/if}
        <p class="text-sm">
          {answerText}
        </p>
      </div>

      {#if themes?.length > 0}
        <footer class="flex items-center flex-wrap gap-2 mt-4">
          <small class="text-xs text-neutral-500"> Themes: </small>

          {#each themes as theme (theme)}
            <Tag variant="dark">
              {theme}
            </Tag>
          {/each}
        </footer>
      {/if}
    </article>
  </Panel>
</div>

<style>
  a:hover h3 {
    color: var(--color-primary);
  }
  a:hover .question-number {
    color: white;
    background-color: var(--color-primary);
  }
</style>
