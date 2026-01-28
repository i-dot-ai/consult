import type { SaveThemeError } from "../ErrorSavingTheme/ErrorSavingTheme.svelte";
import SelectedThemeCard from "./SelectedThemeCard.svelte";

const consultationId = $state("consultation-id");
const questionId = $state("question-id");

const showError = (error: SaveThemeError) => alert(`Error: ${error.type}`);

const theme = $state({
  id: "theme-id",
  name: "Theme Name",
  description: "Theme description",
  version: 1,
  modified_at: new Date().toISOString(),
  last_modified_by: "user@example.com",
});

export default {
  name: "SelectedThemeCard",
  component: SelectedThemeCard,
  category: "Theme Sign Off",
  props: [
    {
      name: "consultationId",
      value: consultationId,
      type: "string",
    },
    {
      name: "questionId",
      value: questionId,
      type: "string",
    },
    {
      name: "showError",
      value: showError,
      type: "func",
      schema: `(error: SaveThemeError) => void`,
    },
    {
      name: "theme",
      value: theme,
      type: "json",
    },
  ],
  stories: [],
};
