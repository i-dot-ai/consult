<script lang="ts">
  import Switch from "../../inputs/Switch/Switch.svelte";
  import TextInput from "../../inputs/TextInput/TextInput.svelte";
  import Star from "../../svg/material/Star.svelte";
  import RespondentSidebarItem from "./RespondentSidebarItem.svelte";

  let title = $state("Test Title");
  let subtitle = $state("Test subtitle");
  let editable = $state(false);
</script>

<RespondentSidebarItem
  {title}
  {subtitle}
  icon={Star}
  {editable}
  updateSubtitle={(newSubtitle: string) => (subtitle = newSubtitle)}
/>

<hr class="my-8" />

<TextInput
  id="input-title"
  label="Title"
  value={title}
  setValue={(newValue) => (title = newValue)}
/>

<TextInput
  id="input-subtitle"
  label="Subtitle"
  value={subtitle}
  setValue={(newValue) => (subtitle = newValue)}
/>

<div class="w-max">
  <Switch
    id="editable-input"
    label="Editable"
    value={editable}
    handleChange={(newVal) => (editable = newVal)}
  />
</div>
