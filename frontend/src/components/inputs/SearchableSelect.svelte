<script lang="ts">
  // Using melt-ui combobox
  // Docs: https://www.melt-ui.com/docs/builders/combobox

  import clsx from "clsx";

  import {
    createCombobox,
    melt,
    type ComboboxOptionProps,
  } from "@melt-ui/svelte";

  import { fly } from "svelte/transition";
  import MaterialIcon from "../MaterialIcon.svelte";
  import Check from "../svg/material/Check.svelte";
  import KeyboardArrowDown from "../svg/material/KeyboardArrowDown.svelte";
  import Search from "../svg/material/Search.svelte";
  import type { SearchableSelectOption } from "../../global/types";

  export let label: string = "";
  export let handleChange = (_option: SearchableSelectOption) => {};
  export let options: SearchableSelectOption[] = [];
  export let selectedValues: unknown[] = [];
  export let hideArrow: boolean = false;
  export let notFoundMessage: string = "No results found";

  const handleSelectedChange = ({ next }: { next: unknown }) => {
    handleChange(next as SearchableSelectOption);
    return next;
  };

  const toOption = (
    option: SearchableSelectOption,
  ): ComboboxOptionProps<SearchableSelectOption> => ({
    value: option,
    label: option.label,
    disabled: option.disabled,
  });

  const {
    elements: { menu, input, option: meltOption, label: meltLabel },
    states: { open, inputValue, touchedInput, selected: _selected },
    helpers: { isSelected: _isSelected },
  } = createCombobox<SearchableSelectOption>({
    onSelectedChange: handleSelectedChange,
    forceVisible: true,
  });

  $: if (!$open) {
    $inputValue = "";
  }

  $: filteredOptions = $touchedInput
    ? options.filter((option) => {
        return (
          option.label
            .toLowerCase()
            .includes($inputValue.toLowerCase().trim()) ||
          (option.description &&
            option.description
              .toLowerCase()
              .includes($inputValue.toLowerCase().trim()))
        );
      })
    : options;
</script>

<div class="flex flex-col gap-1">
  <label use:melt={$meltLabel}>
    <span class="text-sm font-medium text-neutral-900">
      {label}
    </span>
  </label>

  <div class="relative">
    <div class="absolute left-2 top-1/2 -translate-y-1/2">
      <MaterialIcon color="fill-neutral-400">
        <Search />
      </MaterialIcon>
    </div>
    <input
      use:melt={$input}
      class={clsx([
        "w-full",
        "leading-8",
        "flex",
        "items-center",
        "justify-between",
        "rounded",
        "bg-white",
        "px-3",
        "pr-12",
        "text-black",
        "border",
        "border-neutral-300",
        "pl-8",
      ])}
      placeholder="Select themes..."
    />
    {#if !hideArrow}
      <div
        class={clsx([
          "absolute",
          "right-2",
          "top-1/2",
          "z-10",
          "-translate-y-1/2",
          "text-neutral-900",
          "transition-transform",
          "-rotate-90",
          $open && "rotate-0",
        ])}
      >
        <MaterialIcon color="fill-neutral-700">
          <KeyboardArrowDown />
        </MaterialIcon>
      </div>
    {/if}
  </div>
</div>

{#if $open}
  <ul
    class={clsx([
      "z-10",
      "flex",
      "max-h-[300px]",
      "flex-col",
      "overflow-hidden",
      "rounded",
      "shadow",
    ])}
    use:melt={$menu}
    transition:fly={{ duration: 150, y: -5 }}
  >
    <!-- svelte-ignore a11y-no-noninteractive-tabindex -->
    <div
      class={clsx([
        "flex",
        "max-h-full",
        "flex-col",
        "gap-0",
        "overflow-y-auto",
        "bg-white",
        "px-2",
        "py-2",
        "text-black",
      ])}
      tabindex="0"
    >
      {#each filteredOptions as option, index (index)}
        <li
          use:melt={$meltOption(toOption(option))}
          class={clsx([
            "relative",
            "cursor-pointer",
            "scroll-my-2",
            "rounded-md",
            "py-2",
            "pl-4",
            "pr-4",
            "hover:bg-neutral-100",
            "data-[highlighted]:bg-neutral-200",
            "data-[highlighted]:text-neutral-900",
            "data-[disabled]:opacity-50",
          ])}
        >
          {#if selectedValues.includes(option.value)}
            <div class="check absolute left-2 top-1/2 z-10 text-neutral-900">
              <MaterialIcon color="fill-neutral-700">
                <Check />
              </MaterialIcon>
            </div>
          {/if}
          <div class="pl-4">
            <span class="font-medium">
              {option.label}
            </span>
            {#if option.description}
              <span class="block text-sm opacity-75">
                {option.description}
              </span>
            {/if}
          </div>
        </li>
      {:else}
        <li class="relative cursor-pointer rounded-md py-1 pl-8 pr-4">
          {notFoundMessage}
        </li>
      {/each}
    </div>
  </ul>
{/if}

<style lang="postcss">
  .check {
    @apply absolute left-2 top-1/2 text-neutral-500;
    translate: 0 calc(-50% + 1px);
  }
</style>
