<script lang="ts">
  interface Props {
    fill?: boolean;
  }

  let { fill }: Props = $props();
</script>

{#if fill}
  <path
    xmlns="http://www.w3.org/2000/svg"
    d="M200-80v-760h640l-80 200 80 200H280v360h-80Z"
  />
{:else}
  <path
    d="M200-80v-760h640l-80 200 80 200H280v360h-80Zm80-440h442l-48-120 48-120H280v240Zm0 0v-240 240Z"
  />
{/if}
