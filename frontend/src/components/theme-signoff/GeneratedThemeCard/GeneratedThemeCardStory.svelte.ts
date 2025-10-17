import GeneratedThemeCard from "./GeneratedThemeCard.svelte";

let selectedThemes = $state([]);
let theme = $state({
  id: "theme-id",
  name: "Theme Name",
  description: "Theme description",
});
let answers = $state(["Answer 1", "Answer 2"]);
let level = $state(0);
let leftPadding = $state(1);
let handleSelect = (theme) =>
  alert(`Select theme event triggered with: ${theme}`);

export default {
  name: "GeneratedThemeCard",
  component: GeneratedThemeCard,
  category: "Theme Signoff",
  props: [
    {
      name: "selectedThemes",
      value: selectedThemes,
      type: "json",
    },
    {
      name: "theme",
      value: theme,
      type: "json",
    },
    {
      name: "answers",
      value: answers,
      type: "json",
    },
    {
      name: "level",
      value: level,
      type: "number",
    },
    {
      name: "leftPadding",
      value: leftPadding,
      type: "number",
    },
    {
      name: "handleSelect",
      value: handleSelect,
      type: "func",
      schema: `(theme: GeneratedTheme) => void`,
    },
  ],
  stories: [],
};
