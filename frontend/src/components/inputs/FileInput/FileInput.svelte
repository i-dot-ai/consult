<script lang="ts">
  import clsx from "clsx";

  import { slide } from "svelte/transition";

  import Button from "../Button/Button.svelte";
  import MaterialIcon from "../../MaterialIcon.svelte";
  import Upload from "../../svg/material/Upload.svelte";
  import Close from "../../svg/material/Close.svelte";

  interface Props {
    id: string;
    title: string;
    subtitle: string;
    accept: string;
    maxSize?: number;
    multiple?: boolean;
    onConfirm: (files: File[]) => void;
  }

  let {
    id = "file-input",
    title = "Drag and drop files here",
    subtitle,
    accept,
    maxSize = Infinity,
    multiple = true,
    onConfirm = () => {},
  }: Props = $props();

  let files: File[] = $state([]);
  let isDragging = $state(false);
  let errorMessage = $state("");
  let inputEl;

  const FILE_SIZE_ERROR = "File size limit exceeded";

  function removeFile(fileIndex: number) {
    const dataTransfer = new DataTransfer();

    for (let i = 0; i < files.length; i++) {
      if (i !== fileIndex) {
        dataTransfer.items.add(inputEl!.files.item(i)!);
      }
    }

    updateInputFiles(dataTransfer);
  }

  function isFilesCorrectSize(files: FileList) {
    let totalSize = 0;
    for (const file of files) {
      totalSize += file.size;
    }
    return totalSize <= maxSize;
  }

  function isFilesValid(files: FileList) {
    if (!isFilesCorrectSize(files)) {
      errorMessage = FILE_SIZE_ERROR;
      return false;
    }
    errorMessage = "";
    return true;
  }

  function updateInputFiles(dataTransfer: DataTransfer) {
    if (!isFilesValid(dataTransfer.files)) {
      return;
    }

    inputEl!.files = dataTransfer.files;
    inputEl!.dispatchEvent(new Event("change", { bubbles: true }));
  }

  function handleFileDrop(dataTransfer: DataTransfer) {
    const droppedFiles = dataTransfer.files;

    if (droppedFiles) {
      const dataTransfer = new DataTransfer();

      // Only add first file if not multiple,
      // otherwise add all files
      for (let i = 0; i < droppedFiles.length; i++) {
        if (i === 0 || multiple) {
          dataTransfer.items.add(droppedFiles.item(i)!);
        }
      }

      updateInputFiles(dataTransfer);
    }
  }

  function getSizeText(bytes: number, decimals = 2) {
    if (bytes === 0) {
      return '0 Bytes';
    };
    const UNITS = ['Bytes', 'KB', 'MB', 'GB', 'TB'];
    const kilo = 1024;
    const clampedDecimals = decimals < 0 ? 0 : decimals;
    const result = Math.floor(Math.log(bytes) / Math.log(kilo));
    return parseFloat((bytes / Math.pow(kilo, result)).toFixed(clampedDecimals)) + ' ' + UNITS[result];
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
  ondragleave={() => {
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

  <small class={clsx(["text-neutral-500", "text-xs"])}>{subtitle}</small>

  {#if errorMessage}
    <small transition:slide class="text-red-500">{errorMessage}</small>
  {/if}

  <input
    bind:this={inputEl}
    {id}
    {multiple}
    {accept}
    class="sr-only"
    type="file"
    onchange={(e) => {
      const newFiles = (e.target as HTMLInputElement)!.files!;
      if (!isFilesValid(newFiles)) {
        return;
      }
      files = Array.from(newFiles);
    }}
    data-testid="file-input"
  />

  <ul class={clsx(["text-xs", "text-neutral-500"])}>
    {#each files as file, i (i)}
      <li class="my-0.5">
        <div class={clsx(["flex", "items-center", "gap-1"])}>
          <Button
            variant="ghost"
            handleClick={(e) => {
              e.stopPropagation();
              e.preventDefault();
              removeFile(i);
            }}
            ariaLabel={`Remove file ${file.name}`}
          >
            <MaterialIcon color="fill-neutral-500" size="0.8rem">
              <Close />
            </MaterialIcon>
          </Button>

          <p>{file.name} • {getSizeText(file.size)}</p>
        </div>
      </li>
    {/each}
  </ul>

  <div
    class={clsx([
      "w-full",
      "flex",
      "items-center",
      "justify-center",
      "gap-1",
      "my-2",
    ])}
  >
    <Button
      size="sm"
      handleClick={(e) => {
        // does not propagate automatically
        const newEvent = new MouseEvent(e.type, e);
        (e.target as HTMLElement)!.closest("label")!.dispatchEvent(newEvent);
      }}
    >
      Choose file
    </Button>

    {#if files.length > 0}
      <Button variant="approve" handleClick={() => onConfirm(files)} size="sm">
        Confirm
      </Button>
    {/if}
  </div>
</label>
