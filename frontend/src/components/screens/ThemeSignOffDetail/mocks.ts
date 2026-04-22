import { getApiGetGeneratedThemesUrl, getApiGetSelectedThemesUrl, getApiGetSelectedThemeUrl, getApiQuestionUrl } from "../../../global/routes";

interface Theme {
  id: string;
  name: string;
  description: string;
  version?: number;
  modified_at?: string;
  last_modified_by?: string;
  children?: Theme[];
  selectedtheme_id?: string | null;
}

let selectedThemes: Theme[] = [
  {
    "id": "dc1c0652-1042-4b99-b832-89a8f80c3f57",
    "name": "Innovative packaging",
    "description": "Ideas for innovative packaging solutions.",
    "version": 1,
    "modified_at": "2026-03-26T15:26:11.485448Z",
    "last_modified_by": "email@example.com"
  }
];

let candidateThemes: Theme[] = [
  {
      "id": "5021fc03-2772-442e-b860-de11ccf4631f",
      "name": "More innovative",
      "description": "Innovative ideas to improve chocolate bar regulations.",
      "children": [
          {
              "id": "afc3d38d-5553-494d-a8c5-ba11d6990364",
              "name": "Innovative packaging",
              "description": "Ideas for innovative packaging solutions.",
              "children": [],
              "selectedtheme_id": "dc1c0652-1042-4b99-b832-89a8f80c3f57"
          },
          {
              "id": "1da5d250-6533-4ac3-80e3-e6a70a4e6b91",
              "name": "New flavor combinations",
              "description": "Exploring new flavor combinations.",
              "children": [
                  {
                      "id": "7a9e2914-9bcf-4006-ae4b-9ff3dbd611f5",
                      "name": "Exotic flavors",
                      "description": "Incorporating exotic flavors.",
                      "children": [],
                      "selectedtheme_id": null
                  },
                  {
                      "id": "2c048018-fcdc-4dc8-a2bd-1128f9306214",
                      "name": "Fusion flavors",
                      "description": "Creating fusion flavors.",
                      "children": [],
                      "selectedtheme_id": null
                  }
              ],
              "selectedtheme_id": null
          }
      ],
      "selectedtheme_id": null
  },
  {
      "id": "90c7b0ec-8d72-47dd-a225-5c548be4c1d5",
      "name": "Healthier options",
      "description": "It should encourage healthier options.",
      "children": [],
      "selectedtheme_id": null
  },
  {
      "id": "53970026-460d-4eb3-bb7b-f8d52ca7523e",
      "name": "Clearer guidelines",
      "description": "It should include clearer guidelines.",
      "children": [],
      "selectedtheme_id": null
  },
  {
      "id": "369195cf-8c98-4c54-93f9-d9ea1366c1d1",
      "name": "Fair trade practices",
      "description": "It should promote fair trade practices.",
      "children": [],
      "selectedtheme_id": null
  },
  {
      "id": "2e0fc290-1a76-4704-acb8-32fc3b9942e2",
      "name": "Sustainability",
      "description": "It should focus on sustainability.",
      "children": [],
      "selectedtheme_id": null
  },
  {
      "id": "ff047d2d-84b5-4e1c-aeb9-86e928ccc020",
      "name": "Transparent labeling",
      "description": "It should have transparent labeling.",
      "children": [],
      "selectedtheme_id": null
  }
];

function flatten(themes: Theme[]) {
  return themes.reduce((acc: Theme[], curr: Theme) => {
    acc.push(curr);

    if (curr.children && Array.isArray(curr.children)) {
      acc.push(...flatten(curr.children));
    }

    return acc;
  }, []);
}

function getCandidateTheme(themeId: string) {
  const flatCandidateThemes = flatten(candidateThemes);
  return flatCandidateThemes.find(theme => theme.id === themeId);
}

function selectTheme(themeId: string) {
  const candidateTheme = getCandidateTheme(themeId);
  const newSelectedThemeId = getRandomString();

  const newSelectedTheme = {
    "id": newSelectedThemeId,
    "name": candidateTheme!.name,
    "description": candidateTheme!.description,
    "version": 1,
    "modified_at": new Date().toISOString(),
    "last_modified_by": "email@example.com",
  };

  selectedThemes = [...selectedThemes, newSelectedTheme!];
  candidateThemes = updateCandidateThemeSelectedId(candidateThemes, themeId, newSelectedThemeId);
}

function updateCandidateThemeSelectedId(themes: Theme[], themeId: string, newSelectedThemeId: string) {
  return themes.map((theme): Theme => {
    const updatedTheme = theme.id === themeId
      ? { ...theme, selectedtheme_id: newSelectedThemeId }
      : theme;

    if (updatedTheme.children && Array.isArray(updatedTheme.children)) {
      return {
        ...updatedTheme,
        children: updateCandidateThemeSelectedId(updatedTheme.children, themeId, newSelectedThemeId)
      }
    }

    return updatedTheme;
  })
}

export const CONSULTATION_ID = "test-consultation";
export const QUESTION_ID = "test-question";

export const candidateThemeSelectMock = { 
  regexp: "*host/api/consultations/:consultationId/questions/:questionId/candidate-themes/:themeId/select/",
  method: "POST",
  callback: (body: { params: { themeId: string } }) => {
    selectTheme(body.params.themeId);
  },
};

export const questionMock = {
  url: getApiQuestionUrl(CONSULTATION_ID, QUESTION_ID),
  body: {
    "id": "b20f35ee-411b-4746-9029-1e9b02610dea",
    "number": 4,
    "total_responses": 100,
    "question_text": "What are your thoughts on how the current chocolate bar regulations could be improved to better address consumer needs and industry standards?",
    "has_free_text": true,
    "has_multiple_choice": false,
    "multiple_choice_answer": [],
    "proportion_of_audited_answers": 0,
    "theme_status": "draft"
  }
};

export const selectedThemesGetMock = {
  url: getApiGetSelectedThemesUrl(CONSULTATION_ID, QUESTION_ID),
  body: () => ({
    "count": selectedThemes.length,
    "next": null,
    "previous": null,
    "results": selectedThemes,
  }),
};

export const selectedThemesCreateMock = {
  url: getApiGetSelectedThemesUrl(CONSULTATION_ID, QUESTION_ID),
  method: "POST",
  body: (options: { body: string }) => {
    const data = JSON.parse(options.body);

    const newSelectedTheme = {
      "id": getRandomString(),
      "name": data.name,
      "description": data.description,
      "version": 1,
      "modified_at": new Date().toISOString(),
      "last_modified_by": "email@example.com",
    };

    selectedThemes = [...selectedThemes, newSelectedTheme];

    return newSelectedTheme;
  }
}

export const selectedThemesEditMock = {
  regexp: "*host" + getApiGetSelectedThemeUrl(CONSULTATION_ID, QUESTION_ID, ":themeId"),
  method: "PATCH",
  body: (
    { body, params }: { body: string, params: { themeId: string } },
  ) => {
    const data = JSON.parse(body);
    const themeId = params.themeId;

    const selectedTheme = selectedThemes.find(theme => theme.id === themeId);

    selectedTheme!.name = data.name;
    selectedTheme!.description = data.description;
    selectedTheme!.version = selectedTheme!.version! + 1;
    selectedTheme!.modified_at = new Date().toISOString();

    return selectedTheme;
  }
}

export const candidateThemesGetMock = {
  url: getApiGetGeneratedThemesUrl(CONSULTATION_ID, QUESTION_ID),
  body: () => ({
    "count": candidateThemes.length,
    "next": null,
    "previous": null,
    "results": candidateThemes,
  }),
};

const getRandomString = () => {
  return (Math.random() + 1).toString(36).substring(7);
}