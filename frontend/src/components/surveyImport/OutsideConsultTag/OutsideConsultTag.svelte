<script lang="ts">
  import Tag from "../../Tag/Tag.svelte";
  import MaterialIcon from "../../MaterialIcon.svelte";
  import OpenInNew from "../../svg/material/OpenInNew.svelte";
</script>

<Tag border={true}>
  <span class="flex items-center gap-1">
    <MaterialIcon color="fill-neutral-500" size="0.8rem">
      <OpenInNew />
    </MaterialIcon>
    Happens outside Consult
  </span>
</Tag>
