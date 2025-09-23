<script lang="ts">
  // Using melt-ui select
  // Docs: https://www.melt-ui.com/docs/builders/select

  import clsx from "clsx";

  import { createSelect, melt } from "@melt-ui/svelte";
  import { slide } from "svelte/transition";

  import type { SelectOption } from "../../global/types";
  import { toTitleCase } from "../../global/utils";

  import MaterialIcon from "../MaterialIcon.svelte";
  import KeyboardArrowDown from "../svg/material/KeyboardArrowDown.svelte";
  import Check from "../svg/material/Check.svelte";

  export let value: string = "";
  export let label: string = "Select";
  export let hideLabel: boolean = false;
  export let options: SelectOption[] = [];
  export let placeholder: string = "Select";
  export let handleChange = (nextValue: string) => {};

  function getOption(value: string): SelectOption {
    return (
      options.find((opt) => opt.value === value) || { value: "", label: "" }
    );
  }

  function onSelectedChange({ next }: { next: SelectOption }): SelectOption {
    handleChange(next.value);

    return {
      value: next.value,
      label: toTitleCase(next.label),
    };
  }

  const {
    elements: { trigger, menu, option, label: meltLabel, group, groupLabel },
    states: { selectedLabel, open, selected },
    helpers: { isSelected },
  } = createSelect<string>({
    forceVisible: true,
    onSelectedChange: onSelectedChange as any,
    positioning: {
      placement: "bottom",
      fitViewport: true,
      sameWidth: true,
    },
  });

  $: selected.set(getOption(value));
</script>

<div class="flex flex-col gap-1 text-sm w-full">
  <!-- svelte-ignore a11y-label-has-associated-control - $label contains the 'for' attribute -->
  <label
    use:melt={$meltLabel}
    class={clsx(["block", "text-neutral-900", hideLabel && "sr-only"])}
  >
    {label}
  </label>

  <button
    class={clsx([
      "flex",
      "items-center",
      "justify-between",
      "min-w-[8rem]",
      "px-2",
      "py-1",
      "rounded",
      "bg-neutral-100",
      "text-nautral-700",
      "shadow",
      "transition-opacity",
      "hover:opacity-90",
    ])}
    use:melt={$trigger}
    aria-label={label}
  >
    {$selectedLabel || placeholder}

    <MaterialIcon color="fill-neutral-800">
      <KeyboardArrowDown />
    </MaterialIcon>
  </button>

  {#if $open}
    <div
      use:melt={$menu}
      transition:slide
      class={clsx([
        "z-10",
        "flex",
        "max-h-[300px]",
        "flex-col",
        "overflow-y-auto",
        "rounded-lg",
        "bg-white",
        "p-1",
        "shadow",
        "focus:!ring-0",
      ])}
    >
      <div use:melt={$group("default")}>
        <div
          use:melt={$groupLabel("default")}
          class={clsx([
            "py-1",
            "px-4",
            "font-semibold",
            "capitalize",
            "text-neutral-800",
          ])}
        >
          {""}
        </div>

        {#each options as optionItem}
          <div
            class={[
              "flex",
              "justify-start",
              "items-center",
              "gap-1",
              "relative",
              "mb-1",
              "py-1",
              "px-2",
              "last:mb-0",
              "text-sm",
              "cursor-pointer",
              "rounded",
              "text-neutral-800",
              "hover:bg-neutral-100",
              "focus:z-10",
              "focus:text-neutral-700",
              "data-[highlighted]:bg-neutral-100",
              "data-[highlighted]:text-neutral-900",
              "data-[highlighted]:border",
              "data-[highlighted]:border-yellow-400",
              "data-[disabled]:opacity-50",
              $isSelected(optionItem.value) ? "bg-neutral-100" : "white",
            ]}
            use:melt={$option({
              value: optionItem.value,
              label: optionItem.value,
            })}
          >
            {optionItem.label}

            {#if $isSelected(optionItem.value)}
              <MaterialIcon color="fill-neutral-500">
                <Check />
              </MaterialIcon>
            {/if}
          </div>
        {/each}
      </div>
    </div>
  {/if}
</div>
