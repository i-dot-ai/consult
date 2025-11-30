<script lang="ts">
  import { type Snippet } from "svelte";

  interface Props {
    summaryText: string;
    children: Snippet;
    open?: boolean;
  }

  let { summaryText, children, open = false }: Props = $props();
</script>

<details
  class="mb-5 text-base leading-5 text-neutral-900 md:text-lg md:leading-6"
  {open}
>
  <summary class="relative cursor-pointer text-primary hover:underline">
    <span class="underline-offset-2">
      {summaryText}
    </span>
  </summary>
  <div class="ml-6 border-l-4 border-neutral-400 pl-6 pt-4">
    {@render children()}
  </div>
</details>
