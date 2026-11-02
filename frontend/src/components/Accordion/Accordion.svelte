<script lang="ts">
  import clsx from "clsx";

  import { slide } from "svelte/transition";
  import { type Component, type Snippet } from "svelte";

  import Button from "../inputs/Button/Button.svelte";
  import MaterialIcon from "../MaterialIcon.svelte";
  import ChevronRight from "../svg/material/ChevronRight.svelte";
  import Close from "../svg/material/Close.svelte";

  export interface Props {
    title: Snippet;
    content: Snippet;
    variant?: "light" | "gray" | "gray-white" | "warning" | "ghost";
    Icon?: Component;
    onClose?: () => void;
    onClick?: () => void;
    ariaLabel?: string;
    initialExpanded?: boolean;
  }

  let {
    title,
    content,
    variant = "light",
    Icon,
    onClose,
    onClick,
    ariaLabel,
    initialExpanded,
  }: Props = $props();

  let expanded = $state(initialExpanded);

  function getButtonVariant() {
    if (variant === "gray") {
      return "gray";
    }
    if (variant === "warning") {
      return "warning";
    }
    if (variant === "ghost") {
      return "gray";
    }
    return "default";
  }

  export function open() {
    expanded = true;
  }

  export function close() {
    expanded = false;
  }
</script>

<Button
  variant={getButtonVariant()}
  handleClick={() => {
    expanded = !expanded;

    if (onClick) {
      onClick();
    }
  }}
  fullWidth={true}
  {ariaLabel}
>
  <div class="flex w-full items-center justify-between gap-2">
    <div class={clsx(["flex", "gap-1", "items-center"])}>
      {#if Icon}
        <div class={clsx(["self-start", "shrink-0", "my-2.5", "mx-1"])}>
          <MaterialIcon
            color={variant === "warning"
              ? "fill-yellow-600"
              : "fill-neutral-600"}
            size="1.2rem"
          >
            <Icon />
          </MaterialIcon>
        </div>
      {/if}

      {@render title()}
    </div>

    <div
      class={clsx([
        "flex",
        "items-center",
        "gap-0.5",
        "shrink-0",
        "mx-1",
        Icon && clsx(["my-2.5", "self-start"]),
      ])}
    >
      <div class={clsx(["transition-transform", expanded && "rotate-90"])}>
        <MaterialIcon
          color={variant === "warning" ? "fill-yellow-500" : "fill-neutral-500"}
        >
          <ChevronRight />
        </MaterialIcon>
      </div>

      {#if onClose}
        <Button
          handleClick={(e) => {
            e.stopPropagation();
            onClose();
          }}
          variant="ghost"
          ariaLabel={`close ${ariaLabel || "accordion"}`}
        >
          <MaterialIcon
            color={variant === "warning"
              ? "fill-yellow-500"
              : "fill-neutral-500"}
          >
            <Close />
          </MaterialIcon>
        </Button>
      {/if}
    </div>
  </div>
</Button>

{#if expanded && content}
  <div
    transition:slide
    class={clsx([
      variant === "light" && "bg-white border-neutral-300 p-4",
      variant === "gray" && "bg-neutral-100 border-neutral-300 p-4",
      variant === "gray-white" && "bg-neutral-100 border-neutral-300 p-4",
      variant === "warning" && "bg-yellow-50 border-yellow-300 p-4",
      variant === "ghost" && "bg-transparent border-transparent p-0 pt-2",
      "rounded-b-lg border border-t-0",
    ])}
  >
    {@render content()}
  </div>
{/if}
