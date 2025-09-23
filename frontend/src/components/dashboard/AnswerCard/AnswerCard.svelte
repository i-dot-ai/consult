<script lang="ts">
  import clsx from "clsx";

  import type { ResponseTheme } from "../../../global/types";
  import { applyHighlight } from "../../../global/utils";
  import { themeFilters } from "../../../global/state.svelte";

  import Button from "../../inputs/Button/Button.svelte";
  import Panel from "../Panel/Panel.svelte";
  import Tag from "../../Tag/Tag.svelte";
  import MaterialIcon from "../../MaterialIcon.svelte";
  import Diamond from "../../svg/material/Diamond.svelte";
  import EditPanel from "../EditPanel/EditPanel.svelte";
  import FlagButton from "../FlagButton/FlagButton.svelte";
  import Person from "../../svg/material/Person.svelte";
  import { getRespondentDetailUrl, Routes } from "../../../global/routes";

  interface Props {
    consultationId?: string;
    questionId?: string;
    answerId?: string;
    displayId?: string;
    text?: string;
    demoData?: string[];
    evidenceRich?: boolean;
    multiAnswers?: string[];
    themes?: ResponseTheme[];
    themeOptions?: ResponseTheme[];
    skeleton?: boolean;
    highlightText?: string;
    isFlagged?: boolean;
    isEdited?: boolean;
    resetData?: () => void;
  }

  let {
    consultationId = "",
    questionId = "",
    answerId = "",
    displayId = "",
    text = "",
    demoData = [],
    evidenceRich = false,
    multiAnswers = [],
    themes = [],
    themeOptions = [],
    skeleton = false,
    highlightText = "",
    isFlagged = false,
    isEdited = false,
    resetData = () => {},
  }: Props = $props();

  let editing: boolean = $state(false);
</script>

<Panel>
  <article
    class={clsx([
      "flex",
      "flex-col",
      "gap-2",
      "w-full",
      "rounded-xl",
      "leading-[1.5rem]",
      "transition-all",
      "duration-300",
      editing && clsx(["outline", "outline-4", "outline-teal", "p-2"]),
    ])}
  >
    <header
      class={clsx([
        "flex",
        "justify-between",
        "items-start",
        "gap-1",
        "flex-wrap",
        "text-sm",
        "flex-col-reverse",
        "md:flex-row",
      ])}
    >
      {#if (demoData && demoData.length > 0) || evidenceRich || skeleton}
        <div
          class={clsx([
            "flex",
            "flex-wrap",
            "items-center",
            "gap-2",
            "max-w-[75%]",
          ])}
        >
          {#if skeleton}
            {#each "_".repeat(3) as _}
              <div class="blink">
                <Tag>
                  <span
                    class="text-xs bg-neutral-100 text-neutral-100 select-none"
                    >skeleton</span
                  >
                </Tag>
              </div>
            {/each}
          {:else}
            {#each demoData as demoDataItem}
              <Tag>
                <span class="text-xs">{demoDataItem.replaceAll("'", "")}</span>
              </Tag>
            {/each}
          {/if}

          {#if evidenceRich && !skeleton}
            <Tag variant="warning">
              <MaterialIcon size="1rem" color="fill-yellow-700">
                <Diamond />
              </MaterialIcon>

              <span class="text-xs">Evidence-rich</span>
            </Tag>
          {/if}

          {#if isEdited && !skeleton}
            <Tag variant="success">
              <span class="text-xs">Edited</span>
            </Tag>
          {/if}
        </div>
      {/if}

      <div class="flex items-center gap-2">
        {#if !skeleton}
          <FlagButton
            {consultationId}
            {questionId}
            {answerId}
            {resetData}
            {isFlagged}
          />

          <EditPanel
            {consultationId}
            {questionId}
            {answerId}
            {themes}
            {themeOptions}
            {evidenceRich}
            {resetData}
            setEditing={(val: boolean) => (editing = val)}
          />
        {/if}

        <small
          title="Respondent ID"
          class={clsx([
            "whitespace-nowrap",
            skeleton && "bg-neutral-100 text-neutral-100 select-none blink",
          ])}
        >
          {#if skeleton}
            SKELETON
          {:else}
            <div class="m-auto">
              <Button
                size="xs"
                handleClick={() => {
                  location.href = getRespondentDetailUrl(
                    consultationId,
                    displayId,
                  );
                }}
              >
                <MaterialIcon color="fill-neutral-500" size="0.8rem">
                  <Person />
                </MaterialIcon>

                <span class="ml-1">ID: {displayId}</span>
              </Button>
            </div>
          {/if}
        </small>
      </div>
    </header>

    {#if skeleton}
      <p
        class={clsx([
          "bg-neutral-100",
          "text-neutral-100",
          "select-none",
          "blink",
        ])}
      >
        {"SKELETON ".repeat(20)}
      </p>
    {:else if text}
      <p>
        {@html applyHighlight(text, highlightText)}
      </p>
    {/if}

    {#if multiAnswers && multiAnswers.length > 0 && !skeleton}
      <ul class={clsx(["flex", "gap-2", "flex-wrap", "my-1"])}>
        {#each multiAnswers as multiAnswer}
          <Tag>
            <span class="text-xs">{multiAnswer}</span>
          </Tag>
        {/each}
      </ul>
    {/if}

    {#if themes && themes.length > 0 && !skeleton}
      <footer class={clsx(["flex", "items-center", "gap-1", "flex-wrap"])}>
        <small class="text-neutral-500"> Themes: </small>
        {#each themes as theme}
          <Button
            handleClick={() => themeFilters.update(theme.id)}
            highlighted={themeFilters.filters.includes(theme.id)}
            highlightVariant="light"
            size="xs"
          >
            {theme.name}
          </Button>
        {/each}
      </footer>
    {/if}
  </article>
</Panel>
