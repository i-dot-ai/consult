<script lang="ts">
  import clsx from "clsx";

  import { fade } from "svelte/transition";
  import type { HTMLInputTypeAttribute } from "svelte/elements";

  import Button from "../Button/Button.svelte";
  import MaterialIcon from "../../MaterialIcon.svelte";
  import Close from "../../svg/material/Close.svelte";
  import Search from "../../svg/material/Search.svelte";

  export let inputType: HTMLInputTypeAttribute = "text";
  export let id: string = "";
  export let label: string = "";
  export let hideLabel: boolean = false;
  export let value: string = "";
  export let placeholder: string = "";
  export let autocomplete: string;
  export let name: string;
  export let setValue = (_newValue: string) => {};

  export let variant: "default" | "search" = "default";
</script>

<div class="relative">
  <label for={id} class={clsx([hideLabel && "sr-only"])}>
    {label}
  </label>
  <input
    class={clsx([
      "w-full",
      "mt-1",
      "p-1",
      "border",
      "border-gray-300",
      "rounded-sm",
      "focus:outline-2",
      "focus:outline-yellow-300",
      variant === "search" && "pr-4 pl-8",
    ])}
    type={inputType}
    {id}
    {name}
    {placeholder}
    {value}
    {autocomplete}
    on:input={(e) => setValue((e.target as HTMLInputElement).value)}
  />

  {#if variant === "search" && value}
    <div
      transition:fade={{ duration: 200 }}
      class={clsx([
        "absolute",
        "right-1",
        "top-1/2",
        "-translate-y-1/2 mt-0.5",
      ])}
    >
      <Button variant="ghost" handleClick={() => setValue("")}>
        <MaterialIcon size="1rem" color="black">
          <Close />
        </MaterialIcon>
      </Button>
    </div>
  {/if}

  {#if variant === "search"}
    <div class="absolute left-2 top-1/2 transform -translate-y-1/2 mt-0.5">
      <MaterialIcon color="fill-neutral-400" size="1.2rem">
        <Search />
      </MaterialIcon>
    </div>
  {/if}
</div>

<style>
  input:placeholder-shown {
    text-overflow: ellipsis;
  }
</style>
