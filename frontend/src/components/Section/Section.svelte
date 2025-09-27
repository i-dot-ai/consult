<script lang="ts">
  export let narrow: boolean = false;
</script>

<section
  class={narrow ? "pt-8 pb-16 max-w-4xl mx-auto" : "p-8 mx-[0] md:mx-[5vw]"}
>
  <slot />
</section>
