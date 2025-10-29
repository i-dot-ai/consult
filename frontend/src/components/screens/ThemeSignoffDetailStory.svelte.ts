import ThemeSignoffDetail from "./ThemeSignoffDetail.svelte";

let consultationId = $state("");
let questionId = $state("");

let selectedThemes = $state([]);

let generatedThemes = $state([
  {
    id: "b1a2c3d4-e5f6-7890-abcd-1234567890ab",
    name: "Ethical AI Development",
    description:
      "Ensuring AI systems align with ethical principles and values.",
    children: [
      {
        id: "c2b3a4d5-e6f7-8901-bcde-2345678901bc",
        name: "Educational AI Standards",
        description:
          "Guidelines for AI use in educational institutions and platforms.",
        children: [
          {
            id: "d4e5f6a7-b8c9-0123-def0-5678901234ef",
            name: "AI Use In Schools",
            description: "Measures around AI use in schools",
            children: [],
          },
        ],
      },
      {
        id: "f8c2a1b4-3e6d-4a9f-8b2c-7d5e9a1c2f3b",
        name: "Public-Private Partnerships",
        description:
          "Collaboration frameworks between government and industry.",
        children: [],
      },
    ],
  },
  {
    id: "e5f6a7b8-c9d0-1234-ef01-6789012345f0",
    name: "Continuous Monitoring",
    description:
      "Ongoing oversight of deployed AI systems and their performance.",
    children: [],
  },
]);

export default {
  name: "ThemeSignoffDetail",
  component: ThemeSignoffDetail,
  category: "Theme Signoff",
  props: [
    { name: "consultationId", value: consultationId, type: "text" },
    { name: "questionId", value: questionId, type: "text" },
    { name: "questionDataMock", value: () => ({ "number": 1 }) },

    { name: "generatedThemesMock" , value: () => ({ "results": generatedThemes}) },

    { name: "selectedThemesMock", value: () => ({ "results": selectedThemes }) },

    { name: "removeThemeMock", value: (req) => {
      const themeId = req.url.split("/selected-themes/")[1].replaceAll("/", "");
      selectedThemes = [...selectedThemes].filter(theme => theme.id !== themeId);

      const generatedTheme = findNestedTheme(generatedThemes, (theme) => theme.selectedtheme_id === themeId);
      generatedTheme.selectedtheme_id = null;
    }},

    { name: "createThemeMock", value: (req) => {
      const { name, description } = JSON.parse(req.body);
      const newTheme = {
        "id": (selectedThemes.length + 1).toString(),
        "name": name,
        "description": description,
        "version": 1,
        "last_modified_by": "email@example.com",
        "modified_at": new Date().toISOString(),
      };
      selectedThemes = [...selectedThemes, newTheme];
    }},

    { name: "updateThemeMock", value: (req) => {
      const themeId = req.url.split("/selected-themes/")[1].replaceAll("/", "");
      const { name, description, version } = JSON.parse(req.body);

      const newTheme = {
        "id": themeId,
        "name": name,
        "description": description,
        "version": version,
        "last_modified_by": "email@example.com",
        "modified_at": new Date().toISOString(),
      };

      selectedThemes = [...selectedThemes].map(
        theme => theme.id === themeId ? newTheme : theme
      );
    }},

    { name: "answersMock", value: () =>({ all_respondents: [
        {free_text_answer_text: "Example answer 1"},
        {free_text_answer_text: "Example answer 2"},
        {free_text_answer_text: "Example answer 3"},
      ]
    })},

    { name: "selectGeneratedThemeMock", value: (req) => {
      const themeId = req.url.split("/candidate-themes/")[1].split("/select/")[0];
      
      // Recursively search child themes
      let selectedGeneratedTheme = findNestedTheme(generatedThemes, (theme) => theme.id === themeId);

      const newSelectedThemeId = (selectedThemes.length + 1).toString();

      const newSelectedTheme = {
        id: newSelectedThemeId,
        name: selectedGeneratedTheme?.name,
        description: selectedGeneratedTheme?.description,
        version: 1,
        candidatetheme_id: selectedGeneratedTheme?.id,
        last_modified_by: "email@example.com",
        modified_at: new Date().toISOString(),
      }

      selectedThemes = [...selectedThemes, newSelectedTheme];
      selectedGeneratedTheme.selectedtheme_id = newSelectedThemeId;
    }}
  ],
  stories: [],
};

const findNestedTheme = (themes, compareFunc) => {
  for (const theme of themes) {
    if (compareFunc(theme)) {
      return theme;
    } else if (theme.children?.length > 0) {
      const result = findNestedTheme(theme.children, compareFunc);

      if (result) {
        return result;
      }
    }
  }
}