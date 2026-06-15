import SelectedThemeCard from "./SelectedThemeCard.svelte";

const theme = $state({
  id: "theme-id",
  name: "Theme Name",
  description: "Theme description",
});
const responses = $state(["response 1", "response 2"]);
const removeTheme = $state((themeId: string) =>
  alert(`Remove theme event triggered with: ${themeId}`),
);
const updateTheme = $state((...args: unknown[]) =>
  alert(`Update theme event triggered with: ${args.join(", ")}`),
);

export default {
  name: "SelectedThemeCard",
  component: SelectedThemeCard,
  category: "Finalising Themes",
  props: [
    {
      name: "theme",
      value: theme,
      type: "json",
    },
    {
      name: "responses",
      value: responses,
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
