<script lang="ts">
  import Accordion from "../../Accordion/Accordion.svelte";
  import Panel from "../../dashboard/Panel/Panel.svelte";
  import Button from "../../inputs/Button/Button.svelte";
  import Textarea from "../../inputs/Textarea/Textarea.svelte";
  import TextInput from "../../inputs/TextInput/TextInput.svelte";
  import MaterialIcon from "../../MaterialIcon.svelte";
  import EditSquare from "../../svg/material/EditSquare.svelte";
  import Plus from "../../svg/material/Plus.svelte";
  import Tip from "../../svg/material/Tip.svelte";

  export interface Props {
    initialTitle: string;
    initialDescription: string;
    handleConfirm: (title: string, description: string) => void;
    handleCancel: () => void;
    variant?: "add" | "edit";
  }

  let {
    initialTitle = "",
    initialDescription = "",
    handleConfirm = () => {},
    handleCancel = () => {},
    variant = "add",
  }: Props = $props();

  let title = $state(initialTitle);
  let description = $state(initialDescription);

  const isThemeValid = () => {
    return Boolean(title && description);
  };
</script>

<Panel variant="primary" bg={true} border={true}>
  <div class="flex items-center gap-2">
    {#if variant === "add"}
      <MaterialIcon color="fill-primary">
        <Plus />
      </MaterialIcon>
    {:else}
      <MaterialIcon color="fill-primary">
        <EditSquare />
      </MaterialIcon>
    {/if}

    <h2 class="text-primary">
      {variant === "add" ? "Add Custom Theme" : "Edit Theme"}
    </h2>
  </div>

  <div class="mt-4 text-sm">
    <Accordion variant="gray">
      {#snippet title()}
        <div class="flex gap-2 items-center">
          <MaterialIcon color="fill-neutral-500">
            <Tip />
          </MaterialIcon>
          Creating Effective Themes
        </div>
      {/snippet}

      {#snippet content()}
        <div class="text-xs">
          <h4>Good theme titles:</h4>
          <ul class="list-disc ml-4">
            <li>
              Are specific and descriptive (e.g., "Data Privacy Concerns")
            </li>
            <li>Use clear, jargon-free language</li>
            <li>Focus on the main topic or concern</li>
          </ul>

          <h4 class="mt-2">Good theme descriptions:</h4>
          <ul class="list-disc ml-4">
            <li>Explain what types of responses belong in this theme</li>
            <li>Include key concepts or phrases to look for</li>
            <li>Help categorise responses consistently</li>
          </ul>
        </div>
      {/snippet}
    </Accordion>
  </div>

  <div class="mt-4 text-sm">
    <TextInput
      id="title-input"
      label="Theme Title"
      placeholder="e.g., Data Privacy Concerns"
      value={title}
      setValue={(newTitle) => (title = newTitle.trim())}
    />
  </div>

  <div class="mt-4 text-sm">
    <Textarea
      rows={3}
      id="description-input"
      label="Theme Description"
      placeholder="Describe what responses should be categorised under this theme..."
      value={description}
      setValue={(newVal) => (description = newVal.trim())}
    />
  </div>

  <div class="mt-4">
    <Button
      variant="primary"
      size="sm"
      disabled={!isThemeValid()}
      handleClick={() => {
        handleConfirm(title, description);
      }}
    >
      {variant === "add" ? "Add Theme" : "Save Changes"}
    </Button>

    <Button size="sm" handleClick={() => handleCancel()}>Cancel</Button>
  </div>
</Panel>
