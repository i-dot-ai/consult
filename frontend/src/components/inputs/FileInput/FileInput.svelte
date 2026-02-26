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
  let isDragging = $state(false);
  let inputEl;
</script>

<label
  id="file-input"
  class={clsx([
    "flex",
    "flex-col",
    "items-center",
    "gap-2",
    "p-4",
    "border",
    "border-dashed",
    isDragging ? "border-secondary" : "border-neutral-300",
    isDragging && "bg-neutral-100",
    "hover:border-secondary",
    "rounded-lg",
    "transition-colors",
    "cursor-pointer",
    "text-md",
    "text-neutral-800",
  ])}
  ondragover={(e) => {
    e.preventDefault();
    isDragging = true;
  }}
  ondragleave={(e) => {
    isDragging = false;
  }}
  ondrop={(e) => {
    e.preventDefault();
    isDragging = false;

    const droppedFiles = e.dataTransfer?.files;

    if (droppedFiles) {
      const dataTransfer = new DataTransfer();

      // Only add first file if not multiple,
      // otherwise add all files
      for (let i=0; i<droppedFiles.length; i++) {
        if (i === 0 || multiple) {
          dataTransfer.items.add(droppedFiles.item(i)!);
        }
      }

      inputEl!.files = dataTransfer.files;
      inputEl!.dispatchEvent(new Event('change', { bubbles: true }));
    }
  }}
>
  <MaterialIcon color="fill-neutral-400" size="3rem">
    <Upload />
  </MaterialIcon>

  <span>{title}</span>

  <small class={clsx([
    "text-neutral-500",
    "text-xs",
  ])}>{subtitle}</small>

  <input
    bind:this={inputEl}
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