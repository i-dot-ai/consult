import SelectedThemeCard from "./SelectedThemeCard.svelte";

let theme = $state({
  id: "theme-id",
  name: "Theme Name",
  description: "Theme description",
});
let answers = $state(["Answer 1", "Answer 2"]);
let removeTheme = $state((themeId) =>
  alert(`Remove theme event triggered with: ${themeId}`),
);
let updateTheme = $state((...args) =>
  alert(`Update theme event triggered with: ${args.join(", ")}`),
);

export default {
  name: "SelectedThemeCard",
  component: SelectedThemeCard,
  category: "Theme Signoff",
  props: [
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
      name: "removeTheme",
      value: removeTheme,
      type: "func",
      schema: `(themeId: string) => void`,
    },
    {
      name: "updateTheme",
      value: updateTheme,
      type: "func",
      schema: `(themeId: string, title: string, description: string) => void,`,
    },
  ],
  stories: [],
};
