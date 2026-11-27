<script lang="ts">
  interface Props {
    length: number;
  }

  let { length = 5 }: Props = $props();
</script>

<span
  class="blink w-max select-none bg-text-light-80 text-text-light-80"
  aria-hidden="true"
>
  {"SKELETON ".repeat(length)}
</span>
