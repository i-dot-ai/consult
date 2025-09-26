<script lang="ts">
  import Switch from "../../inputs/Switch/Switch.svelte";
  import TextInput from "../../inputs/TextInput/TextInput.svelte";
  import ThemesTable from "./ThemesTable.svelte";

  let highlightedId: string = $state("");

  let themes = $state([
    {
      id: "theme-1",
      name: "Theme 1",
      description: "This is theme 1",
      count: 10,
      highlighted: false,
      handleClick: () => (highlightedId = "theme-1"),
    },
    {
      id: "theme-2",
      name: "Theme 2",
      description: "This is theme 2",
      count: 20,
      highlighted: false,
      handleClick: () => (highlightedId = "theme-2"),
    },
    {
      id: "theme-3",
      name: "Theme 3",
      description: "This is theme 3",
      count: 30,
      highlighted: false,
      handleClick: () => (highlightedId = "theme-3"),
    },
  ]);
  let totalAnswers = $state(60);
  let skeleton = $state(false);
</script>

<ThemesTable
  themes={themes.map((theme) => ({
    ...theme,
    highlighted: theme.id === highlightedId,
  }))}
  {totalAnswers}
  {skeleton}
/>

<hr class="my-8" />

<TextInput
  id="input-themes"
  label="Themes"
  value={JSON.stringify(themes)}
  setValue={(newValue) => {
    try {
      themes = JSON.parse(newValue);
    } catch {}
  }}
/>

<TextInput
  id="input-total-answerws"
  label="Total Answers"
  value={totalAnswers.toString()}
  setValue={(newValue) => (totalAnswers = parseInt(newValue))}
/>

<div class="w-max">
  <Switch
    id="skeleton-input"
    label="Skeleton"
    value={skeleton}
    handleChange={(newVal) => (skeleton = newVal)}
  />
</div>
