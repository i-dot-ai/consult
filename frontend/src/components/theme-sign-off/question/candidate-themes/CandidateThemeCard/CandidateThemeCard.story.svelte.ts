import type { GeneratedTheme } from "../../../../../global/types";
import CandidateThemeCard from "./CandidateThemeCard.svelte";

const consultationId = $state("consultation-id");
const questionId = $state("question-id");

const theme = $state({
  id: "theme-id",
  name: "Theme Name",
  description: "Theme description",
  selectedtheme_id: null,
});
const collapsedThemes = $state([] as string[]);
const level = $state(0);
const leftPadding = $state(1);

const handleSelect = (theme: GeneratedTheme) =>
  alert(`Select theme event triggered with: ${theme.name}`);

export default {
  name: "CandidateThemeCard",
  component: CandidateThemeCard,
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
      name: "theme",
      value: theme,
      type: "json",
    },
    {
      name: "collapsedThemes",
      value: collapsedThemes,
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
  stories: [
    {
      name: "Nested Levels",
      props: {
        theme: {
          id: "theme-id",
          name: "Top Level Theme",
          description: "Theme level 1",
          children: [
            {
              id: "mid-theme-id",
              name: "Mid Level Theme",
              description: "Theme level 2",
              children: [
                {
                  id: "child-theme-id",
                  name: "Child Theme",
                  description: "Theme level 3",
                },
              ],
            },
          ],
        },
        collapsedThemes: [],
        handleSelect: handleSelect,
      },
    },
    {
      name: "No Answers",
      props: {
        theme: {
          id: "theme-id",
          name: "Top Level Theme",
          description: "Theme level 1",
        },
        collapsedThemes: [],
        handleSelect: handleSelect,
      },
    },
    {
      name: "Disabled",
      props: {
        theme: {
          id: "theme-id",
          name: "Disabled Theme",
          description:
            "This theme is disabled because it is already added as selected theme.",
          selectedtheme_id: "test-theme-id",
        },
        collapsedThemes: [],
        handleSelect: handleSelect,
      },
    },
  ],
};
