import type { GeneratedTheme } from "../../../global/types";
import GeneratedThemeCard from "./GeneratedThemeCard.svelte";

let consultationId = $state("test-consultation");
let questionId = $state("test-question");
let theme = $state({
  id: "theme-id",
  name: "Theme Name",
  description: "Theme description",
  selectedtheme_id: null,
});
let expandedThemes: string[] = $state([]);
let hasNestedThemes = $state(false);
let level = $state(0);
let leftPadding = $state(1);

const handleSelect = (theme: GeneratedTheme) =>
  alert(`Select theme event triggered with: ${theme.name}`);

const responsesMock = () => ({
  all_respondents: [
    { free_text_response: "Answer 1" },
    { free_text_response: "Answer 2" },
  ],
});

const setExpandedThemes = (themeId: string) => {
  if (expandedThemes.includes(themeId)) {
    expandedThemes = expandedThemes.filter(id => id !== themeId);
  } else {
    expandedThemes = [...expandedThemes, themeId];
  }
}

export default {
  name: "GeneratedThemeCard",
  component: GeneratedThemeCard,
  category: "Finalising Themes",
  props: [
    {
      name: "consultationId",
      value: consultationId,
      type: "text",
    },
    {
      name: "questionId",
      value: questionId,
      type: "text",
    },
    {
      name: "theme",
      value: theme,
      type: "json",
    },
    {
      name: "expandedThemes",
      value: expandedThemes,
      type: "json",
    },
    {
      name: "hasNestedThemes",
      value: hasNestedThemes,
      type: "bool",
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
    {
      name: "responsesMock",
      value: responsesMock,
    },
    {
      name: "setExpandedThemes",
      value: setExpandedThemes,
      type: "func",
      schema: `(themeId: string) => void`,
    },
  ],
  stories: [
    {
      name: "Nested Levels",
      props: {
        consultationId: consultationId,
        questionId: questionId,
        selectedThemes: [],
        hasNestedThemes: true,
        level: 0,
        expandedThemes: ["theme-1", "theme-2"],
        setExpandedThemes: setExpandedThemes,
        theme: {
          id: "theme-1",
          name: "Top Level Theme",
          description: "Theme level 1",
          children: [
            {
              id: "theme-2",
              name: "Mid Level Theme",
              description: "Theme level 2",
              children: [
                {
                  id: "theme-3",
                  name: "Child Theme",
                  description: "Theme level 3",
                },
              ],
            },
          ],
        },
        handleSelect: handleSelect,
        responsesMock: responsesMock,
      },
    },
    {
      name: "No Answers",
      props: {
        consultationId: consultationId,
        questionId: questionId,
        selectedThemes: [],
        theme: {
          id: "theme-id",
          name: "Top Level Theme",
          description: "Theme level 1",
        },
        handleSelect: handleSelect,
        responsesMock: () => {},
      },
    },
    {
      name: "Disabled",
      props: {
        consultationId: consultationId,
        questionId: questionId,
        selectedThemes: [],
        theme: {
          id: "theme-id",
          name: "Disabled Theme",
          description:
            "This theme is disabled because it is already added as selected theme.",
          selectedtheme_id: "test-theme-id",
        },
        handleSelect: handleSelect,
        responsesMock: () => {},
      },
    },
  ],
};
