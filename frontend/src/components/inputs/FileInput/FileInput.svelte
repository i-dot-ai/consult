<script lang="ts">
  import type { File } from "buffer";

  import clsx from "clsx";

  import Button from "../Button/Button.svelte";
  import MaterialIcon from "../../MaterialIcon.svelte";
  import Upload from "../../svg/material/Upload.svelte";
  import Close from "../../svg/material/Close.svelte";


  interface Props {
    id: string;
    title: string;
    subtitle: string;
    accept: string;
    multiple?: boolean;
    onConfirm: (files: File[]) => void;
  }

  let {
    id = "file-input",
    title = "Drag and drop files here",
    subtitle,
    accept,
    multiple = true,
    onConfirm = () => {},
  }: Props = $props();

  let files: File[] = $state([]);
  let isDragging = $state(false);
  let inputEl;

  function removeFile(fileIndex: number) {
    const dataTransfer = new DataTransfer();

    for (let i=0; i<files.length; i++) {
      if (i !== fileIndex) {
        dataTransfer.items.add(inputEl!.files.item(i)!);
      }
    }

    updateInputFiles(dataTransfer);
  }

  function updateInputFiles(dataTransfer: DataTransfer) {
    inputEl!.files = dataTransfer.files;
    inputEl!.dispatchEvent(new Event('change', { bubbles: true }));
  }

  function handleFileDrop(dataTransfer: DataTransfer) {
    const droppedFiles = dataTransfer.files;

    if (droppedFiles) {
      const dataTransfer = new DataTransfer();

      // Only add first file if not multiple,
      // otherwise add all files
      for (let i=0; i<droppedFiles.length; i++) {
        if (i === 0 || multiple) {
          dataTransfer.items.add(droppedFiles.item(i)!);
        }
      }

      updateInputFiles(dataTransfer);
    }
  }
</script>

<label
  {id}
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
    handleFileDrop(e.dataTransfer!);
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
    {id}
    {multiple}
    {accept}
    class="sr-only"
    type="file"
    onchange={(e) => files = e.target!.files}
  />

  <ul class={clsx([
    "text-xs",
    "text-neutral-500",
  ])}>
    {#each files as file, i (i)}
      <li class="my-0.5">
        <div class={clsx([
          "flex",
          "items-center",
          "gap-1",
        ])}>
          <Button
            variant="ghost"
            handleClick={(e) => {
              e.stopPropagation();
              e.preventDefault();
              removeFile(i);
            }}
          >
            <MaterialIcon color="fill-neutral-500" size="0.8rem">
              <Close />
            </MaterialIcon>
          </Button>

          <p>{file.name}</p>
        </div>
      </li>
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