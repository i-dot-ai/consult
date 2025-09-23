<script lang="ts">
  import MaterialIcon from "../../MaterialIcon.svelte";
  import Button from "../../inputs/Button/Button.svelte";
  import EditSquare from "../../svg/material/EditSquare.svelte";
  import TextInput from "../../inputs/TextInput/TextInput.svelte";
  import Check from "../../svg/material/Check.svelte";
  import Close from "../../svg/material/Close.svelte";
  import { slide } from "svelte/transition";

  interface Props {
    title: string;
    subtitle: string;
    icon: any;
    editable?: boolean;
    updateSubtitle?: (newSubtitle: string) => void;
  }

  let {
    title = "",
    subtitle = "",
    icon,
    editable = false,
    updateSubtitle = () => {},
  }: Props = $props();

  let stagedSubtitle: string = $state(subtitle);
  let editing: boolean = $state(false);

  const toggleEditing = () => {
    // Reset staged subtitle if exiting edit mode
    if (editing) {
      stagedSubtitle = subtitle;
    }
    editing = !editing;
  };

  $effect(() => {
    stagedSubtitle = subtitle;
  });
</script>

<div class="flex items-start gap-2 mt-4 text-xs">
  <div class="bg-neutral-100 p-1 rounded-lg h-max">
    <MaterialIcon size="1.3rem" color="fill-neutral-700">
      <svelte:component this={icon} />
    </MaterialIcon>
  </div>
  <div class="flex flex-col w-full">
    <div class="flex justify-between items-start">
      <h3 class="uppercase text-neutral-500">{title}</h3>

      {#if editable}
        <div class="-mt-1">
          <Button
            variant="ghost"
            handleClick={toggleEditing}
            testId="edit-button"
          >
            <MaterialIcon color="fill-neutral-700">
              <EditSquare />
            </MaterialIcon>
          </Button>
        </div>
      {/if}
    </div>

    {#if editable && editing}
      <div class="mt-1" transition:slide>
        <TextInput
          id="edit-subtitle-input"
          label="Edit Subtitle"
          hideLabel={true}
          value={stagedSubtitle}
          setValue={(newValue) => (stagedSubtitle = newValue.trim())}
        />
        <div class="flex items-center justify-around gap-2 mt-3">
          <div class="grow">
            <Button
              variant="approve"
              fullWidth={true}
              handleClick={() => {
                updateSubtitle(stagedSubtitle);
                toggleEditing();
              }}
              testId="save-button"
            >
              <div class="flex justify-center w-full gap-2">
                <MaterialIcon color="fill-white">
                  <Check />
                </MaterialIcon>

                Save
              </div>
            </Button>
          </div>
          <div class="grow">
            <Button
              fullWidth={true}
              handleClick={() => toggleEditing()}
              testId="cancel-button"
            >
              <div class="flex justify-center w-full gap-2">
                <MaterialIcon color="fill-neutral-500">
                  <Close />
                </MaterialIcon>

                Cancel
              </div>
            </Button>
          </div>
        </div>
      </div>
    {:else}
      <p>{subtitle}</p>
    {/if}
  </div>
</div>
