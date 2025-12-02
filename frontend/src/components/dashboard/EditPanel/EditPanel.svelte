<script lang="ts">
  import { onMount } from "svelte";
  import { slide } from "svelte/transition";

  import {
    type ResponseTheme,
    type SearchableSelectOption,
  } from "../../../global/types";
  import { createFetchStore, type MockFetch } from "../../../global/stores";
  import { getApiAnswerUrl } from "../../../global/routes";

  import Button from "../../inputs/Button/Button.svelte";
  import Popover from "../../inputs/Popover/Popover.svelte";
  import SearchableSelect from "../../inputs/SearchableSelect.svelte";
  import MaterialIcon from "../../MaterialIcon.svelte";
  import Check from "../../svg/material/Check.svelte";
  import Close from "../../svg/material/Close.svelte";
  import EditSquare from "../../svg/material/EditSquare.svelte";
  import Tag from "../../Tag/Tag.svelte";
  import Title from "../../Title.svelte";
  import TitleRow from "../TitleRow.svelte";

  function removeTheme(id: string) {
    stagedThemes = stagedThemes.filter((theme) => theme.id !== id);
  }
  function addTheme(option: SearchableSelectOption) {
    if (stagedThemes.find((theme) => theme.id === option.value)) {
      return;
    }

    stagedThemes = [
      ...stagedThemes,
      {
        id: option.value,
        name: option.label,
        description: option.description || "",
      },
    ];
  }

  function noChangesStaged() {
    if (stagedEvidenceRich !== evidenceRich) {
      return false;
    }
    if (stagedThemes.length !== themes.length) {
      return false;
    }
    return true;
  }

  async function submit() {
    let actualUpdateAnswer = updateAnswerMock || $answerUpdateStore.fetch;

    if (noChangesStaged()) {
      return;
    }

    await actualUpdateAnswer(
      getApiAnswerUrl(consultationId, answerId),
      "PATCH",
      {
        themes: stagedThemes.map((theme) => ({ id: theme.id })),
        evidenceRich: stagedEvidenceRich,
      },
    );

    if (!$answerUpdateStore.error && !$answerUpdateStore.isLoading) {
      resetData();
    }
  }

  interface Props {
    consultationId: string;
    questionId: string;
    answerId: string;
    themes: ResponseTheme[];
    themeOptions: ResponseTheme[];
    evidenceRich: boolean;
    resetData: () => void;
    setEditing: () => void;
    updateAnswerMock?: MockFetch;
  }

  let {
    consultationId = "",
    answerId = "",
    themes = [],
    themeOptions = [],
    evidenceRich = false,
    resetData = () => {},
    setEditing = () => {},
    updateAnswerMock,
  }: Props = $props();

  let stagedThemes: ResponseTheme[] = $state([]);
  let stagedEvidenceRich = $state(false);
  let panelOpen: boolean = $state(false);

  const answerUpdateStore = createFetchStore();

  onMount(() => {
    resetStaged();
  });

  function resetStaged() {
    stagedThemes = themes ? [...themes] : [];
    stagedEvidenceRich = evidenceRich;
    $answerUpdateStore.isLoading = false;
    $answerUpdateStore.error = "";
  }
</script>

<Popover
  label="Edit response labels"
  arrow={false}
  border={false}
  open={panelOpen}
  handleOpenChange={(newOpen) => {
    panelOpen = newOpen;
    setEditing(newOpen);
    resetStaged();
  }}
>
  <div slot="trigger">
    <MaterialIcon color="fill-neutral-500">
      <EditSquare />
    </MaterialIcon>
  </div>

  <div slot="panel" class="w-full bg-white p-4 shadow-lg" data-testid="panel">
    <TitleRow level={3} title="Edit Response Labels">
      <div slot="aside">
        <Button variant="ghost" handleClick={() => (panelOpen = false)}>
          <MaterialIcon color="fill-neutral-500">
            <Close />
          </MaterialIcon>
        </Button>
      </div>
    </TitleRow>

    <div>
      <Title level={4} text="Themes" />

      <ul
        class="my-1 flex flex-wrap items-center justify-start gap-2 sm:max-w-[30vw]"
      >
        {#each stagedThemes as theme (theme.id)}
          <Tag>
            {theme.name}

            <Button variant="ghost" handleClick={() => removeTheme(theme.id)}>
              <MaterialIcon color="fill-neutral-500">
                <Close />
              </MaterialIcon>
            </Button>
          </Tag>
        {/each}
      </ul>

      <div class="my-2">
        <SearchableSelect
          label="Add Themes"
          options={themeOptions.map((theme) => ({
            value: theme.id,
            label: theme.name,
            description: theme.description,
            disabled: false,
          }))}
          selectedValues={stagedThemes.map((theme) => theme.id)}
          handleChange={(option: SearchableSelectOption) => {
            if (option.value) {
              addTheme(option.value);
            }
          }}
        />
      </div>
    </div>

    <div class="my-2">
      <Title level={4} text="Evidence-rich" />

      <div class="my-1 flex items-center gap-2">
        <Button
          size="xs"
          handleClick={() => (stagedEvidenceRich = true)}
          highlighted={stagedEvidenceRich}
          highlightVariant="approve"
        >
          Evidence-rich
        </Button>

        <Button
          size="xs"
          handleClick={() => (stagedEvidenceRich = false)}
          highlighted={!stagedEvidenceRich}
          highlightVariant="approve"
        >
          Not evidence-rich
        </Button>
      </div>
    </div>

    <hr class="my-4" />

    {#if $answerUpdateStore.error}
      <small class="block my-2 text-red-500" transition:slide
        >{$answerUpdateStore.error}</small
      >
    {/if}

    <div class="flex w-full justify-end">
      <div class="ml-1 w-1/2">
        <Button
          variant="approve"
          size="sm"
          handleClick={() => submit()}
          fullWidth={true}
        >
          <div class="flex w-full items-center justify-center gap-2 py-0.5">
            <div class="shrink-0">
              <MaterialIcon>
                <Check />
              </MaterialIcon>
            </div>

            <span class="whitespace-nowrap">
              {$answerUpdateStore.isLoading ? "Saving..." : "Save Changes"}
            </span>
          </div>
        </Button>
      </div>
    </div>
  </div>
</Popover>
