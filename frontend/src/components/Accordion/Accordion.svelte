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
    variant?: "light" | "gray" | "warning";
    Icon?: Component;
    onClose?: () => void;
  }

  let { title, content, variant = "light", Icon, onClose }: Props = $props();

  let expanded = $state(false);

  function getButtonVariant() {
    if (variant === "gray") {
      return "gray";
    }
    if (variant === "warning") {
      return "warning";
    }
    return "default";
  }
</script>

<Button
  variant={getButtonVariant()}
  handleClick={() => (expanded = !expanded)}
  fullWidth={true}
>
  <div class="flex w-full items-center justify-between gap-2">
    <div class={clsx([
      "flex",
      "gap-1",
      "items-center",
    ])}>
      {#if Icon}
        <MaterialIcon
          color={variant === "warning"
            ? "fill-yellow-600"
            : "fill-neutral-600"
          }
          size="1.2rem"
        >
          <Icon />
        </MaterialIcon>
      {/if}

      {@render title()}
    </div>

    <div class={clsx([
      "flex",
      "items-center",
      "gap-0.5",
    ])}>
      <div class={clsx(["transition-transform", expanded && "rotate-90"])}>
        <MaterialIcon
          color={variant === "warning"
            ? "fill-yellow-500"
            : "fill-neutral-500"
          }
        >
          <ChevronRight />
        </MaterialIcon>
      </div>

      {#if onClose}
        <Button handleClick={(e) => {
          e.stopPropagation();
          onClose();
        }} variant="ghost">
          <MaterialIcon
            color={variant === "warning"
              ? "fill-yellow-500"
              : "fill-neutral-500"
            }
          >
            <Close />
          </MaterialIcon>
        </Button>
      {/if}
    </div>
  </div>
</Button>

{#if expanded}
  <div
    transition:slide
    class={clsx([
      variant === "light" && "bg-white",
      variant === "gray" && "bg-neutral-100",
      variant ==="warning" && "border-yellow-300 bg-yellow-50",
      "rounded-b-lg border border-t-0 border-neutral-300 p-4",
    ])}
  >
    {@render content()}
  </div>
{/if}
