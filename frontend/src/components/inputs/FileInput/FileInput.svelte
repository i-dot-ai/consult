<script lang="ts">
  import type { File } from "buffer";

  import clsx from "clsx";

  import MaterialIcon from "../../MaterialIcon.svelte";
  import Upload from "../../svg/material/Upload.svelte";
  import Button from "../Button/Button.svelte";


  interface Props {
    title: string;
    subtitle: string;
    accept: string;
    multiple?: boolean;
    onConfirm: (files: File[]) => void;
  }

  let {
    title = "Drag and drop files here",
    subtitle,
    accept,
    multiple = true,
    onConfirm = () => {},
  }: Props = $props();

  let files: File[] = $state([]);
</script>

<label id="file-input" class={clsx([
  "flex",
  "flex-col",
  "items-center",
  "gap-2",
  "p-4",
  "border",
  "border-dashed",
  "border-neutral-300",
  "hover:border-secondary",
  "rounded-lg",
  "transition-colors",
  "cursor-pointer",
  "text-md",
  "text-neutral-800",
])}>
  <MaterialIcon color="fill-neutral-400" size="3rem">
    <Upload />
  </MaterialIcon>

  <span>{title}</span>

  <small class={clsx([
    "text-neutral-500",
    "text-xs",
  ])}>{subtitle}</small>

  <input
    class="sr-only"
    type="file"
    id="file-input"
    {multiple}
    {accept}
    onchange={(e) => files = e.target!.files}
  />

  <ul class={clsx([
    "text-xs",
    "text-neutral-500",
    "list-disc",
  ])}>
    {#each files as file}
      <li class="my-0.5">{file.name}</li>
    {/each}
  </ul>

  <div class={clsx([
    "w-full",
    "flex",
    "items-center",
    "justify-center",
    "gap-1",
    "my-2",
  ])}>
    <Button size="sm" handleClick={(e) => {
      // does not propagate automatically
      const newEvent = new MouseEvent(e.type, e);
      (e.target as HTMLElement)!.closest("label")!.dispatchEvent(newEvent);
    }}>
      Choose file
    </Button>

    {#if files.length > 0}
      <Button variant="approve" handleClick={() => onConfirm(files)} size="sm">
        Confirm
      </Button>  
    {/if}
  </div>
</label>