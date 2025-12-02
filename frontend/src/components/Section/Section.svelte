<script lang="ts">
  export let narrow: boolean = false;
</script>

<section
  class={narrow ? "mx-auto max-w-4xl pb-16 pt-8" : "mx-[0] p-8 md:mx-[5vw]"}
>
  <slot />
</section>
