<script lang="ts">
    import clsx from "clsx";

    import MaterialIcon from "../MaterialIcon.svelte";
    import ProgressActivity from "../svg/material/ProgressActivity.svelte";

    interface Props {
      size: string;
    }

    let {
      size = "3rem",
    }: Props = $props();
</script>

<div
  style="animation-timing-function: ease-in-out;"
  class={clsx(["animate-spin", "ease-in-out", "w-max", "m-auto"])}
>
  <MaterialIcon color="fill-neutral-300" size={size}>
    <ProgressActivity />
  </MaterialIcon>
</div>