<script lang="ts">
  interface Props {
    length: number;
  }

  let { length = 5 }: Props = $props();
</script>

<span class="blink w-max select-none bg-neutral-200 text-neutral-200">
  {"SKELETON ".repeat(length)}
</span>
