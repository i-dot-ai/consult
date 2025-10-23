import GeneratedThemeCard from "./GeneratedThemeCard.svelte";

let selectedThemes = $state([]);
let theme = $state({
  id: "theme-id",
  name: "Theme Name",
  description: "Theme description",
});
let level = $state(0);
let leftPadding = $state(1);

let handleSelect = (theme) =>
  alert(`Select theme event triggered with: ${theme}`);

let answersMock = () => ({ all_respondents: [
  {free_text_answer_text: "Answer 1"},
  {free_text_answer_text: "Answer 2"},
]})

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
      name: "answersMock",
      value: answersMock,
    },
  ],
  stories: [
    {
      name: "Nested Levels",
      props: {
        selectedThemes: [],
        theme: {
          id: "theme-id",
          name: "Top Level Theme",
          description: "Theme level 1",
          children: [
            {
              id: "theme-id",
              name: "Mid Level Theme",
              description: "Theme level 2",
              children: [
                {
                  id: "theme-id",
                  name: "Child Theme",
                  description: "Theme level 3",
                }
              ]
            }
          ],
        },
        handleSelect: handleSelect,
        answersMock: answersMock,
      }
    },
    {
      name: "No Answers",
      props: {
        selectedThemes: [],
        theme: {
          id: "theme-id",
          name: "Top Level Theme",
          description: "Theme level 1",
        },
        handleSelect: handleSelect,
        answersMock: () => {},
      }
    }
  ],
};
