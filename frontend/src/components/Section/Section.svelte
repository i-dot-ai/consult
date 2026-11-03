<script lang="ts">
  import clsx from "clsx";

  export let narrow: boolean = false;
  // The wide layout pads itself, so gutters only apply with narrow.
  export let gutters: boolean = false;
</script>

<section
  class={clsx([
    narrow ? "mx-auto max-w-4xl pb-16 pt-8" : "mx-0 p-8 md:mx-[5vw]",
    narrow && gutters && "px-4 md:px-6",
  ])}
>
  <slot />
</section>
