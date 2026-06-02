type ConsultationStage = "setup" | "analysis" | "finalising_themes";

export type Theme = {
  name: string;
  description: string;
  key: string;
};

export type Response = {
  free_text?: string;
  chosen_options?: string[];
  themes?: Theme["key"][];
  evidence_rich?: boolean;
};

export type Question = {
  text: string;
  number: number;
  has_free_text: boolean;
  has_multiple_choice: boolean;
  multiple_choice_options?: string[];
  responses?: Response[];
  themes?: Theme[];
};

export type User = {
  email: string;
};

export type Consultation = {
  title: string;
  users: User["email"][];
  stage: ConsultationStage;
  questions?: Question[];
};

export type Fixture = {
  users?: User[];
  consultations?: Consultation[];
};

export type FixtureReference = {
  users?: User[];
  consultation_ids?: string[];
  question_ids?: string[];
};

export const defaultUser: User = {
  email: "email@example.com",
};

const hybridQuestionOptions: string[] = [
  "Yes",
  "No",
  "Don't know",
  "No answer",
];

const hybridQuestionThemes: Theme[] = [
  {
    name: "Standardized framework",
    description:
      "A standardized framework that benefits both consumers and manufacturers.",
    key: "A",
  },
  {
    name: "Innovation",
    description: "Innovation in flavour development",
    key: "B",
  },
];

const hybridQuestionResponses: Response[] = [
  {
    free_text: "",
    chosen_options: [hybridQuestionOptions[0]],
  },
  {
    free_text:
      "Yes, I agree with the proposal as it will create a standardized framework that benefits both consumers and manufacturers.",
    chosen_options: [hybridQuestionOptions[0]],
  },
  {
    free_text:
      "No, I do not agree because I feel the proposed categories are too restrictive and may stifle innovation in flavour development.",
    chosen_options: [hybridQuestionOptions[1]],
  },
  {
    free_text:
      "I agree with the proposal, but I think there should be room for additional categories to accommodate future trends.",
    chosen_options: [hybridQuestionOptions[0], hybridQuestionOptions[2]],
  },
  {
    free_text:
      "I disagree with the proposal as it does not sufficiently account for regional flavour preferences across the UK.",
    chosen_options: [hybridQuestionOptions[1]],
  },
];

const hybridQuestionResponsesWithThemes: Response[] = [
  {
    free_text: "",
    chosen_options: [hybridQuestionOptions[0]],
    themes: ["A", "B"],
    evidence_rich: true,
  },
  {
    free_text:
      "Yes, I agree with the proposal as it will create a standardized framework that benefits both consumers and manufacturers.",
    chosen_options: [hybridQuestionOptions[0]],
    themes: ["A"],
  },
  {
    free_text:
      "No, I do not agree because I feel the proposed categories are too restrictive and may stifle innovation in flavour development.",
    chosen_options: [hybridQuestionOptions[1]],
    themes: ["B"],
  },
  {
    free_text:
      "I agree with the proposal, but I think there should be room for additional categories to accommodate future trends.",
    chosen_options: [hybridQuestionOptions[0], hybridQuestionOptions[2]],
    themes: [],
  },
  {
    free_text:
      "I disagree with the proposal as it does not sufficiently account for regional flavour preferences across the UK.",
    chosen_options: [hybridQuestionOptions[1]],
    themes: ["A"],
  },
];

export const hybridQuestion: Question = {
  text: "Do you agree with the proposal to align the flavour categories of chocolate bars as outlined in the draft guidelines of the Chocolate Bar Regulation for the United Kingdom?",
  number: 1,
  has_free_text: true,
  has_multiple_choice: true,
  multiple_choice_options: ["Yes", "No", "Don't know", "No answer"],
  responses: hybridQuestionResponses,
};

export const hybridQuestionWithThemes: Question = {
  ...hybridQuestion,
  ...{
    responses: hybridQuestionResponsesWithThemes,
    themes: hybridQuestionThemes,
  },
};

const multChoiceQuestionOptions = [
  "Sustainability",
  "Design",
  "Cost-effectiveness",
  "Durability",
  "Brand recognition",
];

export const multChoiceQuestion: Question = {
  text: "Which of the following factors do you believe are important when considering the packaging of chocolate bars? Please select all that apply: a) Sustainability, b) Design, c) Cost-effectiveness, d) Durability, e) Brand recognition.",
  number: 3,
  has_free_text: false,
  has_multiple_choice: true,
  multiple_choice_options: multChoiceQuestionOptions,
  responses: [
    {
      chosen_options: [multChoiceQuestionOptions[0]],
    },
    {
      chosen_options: [multChoiceQuestionOptions[3]],
    },
    {
      chosen_options: [multChoiceQuestionOptions[1]],
    },
    {
      chosen_options: [
        multChoiceQuestionOptions[0],
        multChoiceQuestionOptions[2],
      ],
    },
    {
      chosen_options: [],
    },
    {
      chosen_options: [multChoiceQuestionOptions[1]],
    },
    {
      chosen_options: [multChoiceQuestionOptions[2]],
    },
    {
      chosen_options: [multChoiceQuestionOptions[3]],
    },
    {
      chosen_options: [
        multChoiceQuestionOptions[1],
        multChoiceQuestionOptions[3],
      ],
    },
    {
      chosen_options: [],
    },
  ],
};

export const openQuestionThemes: Theme[] = [
  {
    name: "More innovative",
    description: "Innovative ideas to improve chocolate bar regulations.",
    key: "A",
  },
  {
    name: "Innovative packaging",
    description: "Ideas for innovative packaging solutions.",
    key: "B",
  },
  {
    name: "New flavor combinations",
    description: "Exploring new flavor combinations.",
    key: "C",
  },
];

const openQuestionResponses: Response[] = [
  {
    free_text: "",
  },
  {
    free_text:
      "I believe the current regulations should include clearer guidelines on the sourcing of ingredients to ensure ethical practices and sustainability.",
  },
  {
    free_text:
      "The regulations could be improved by setting specific limits on sugar content to promote healthier options for consumers.",
  },
  {
    free_text:
      "Consideration should be given to standardizing portion sizes to help consumers make informed choices and manage their calorie intake.",
  },
  {
    free_text:
      "It would be beneficial to include mandatory allergen warnings on all packaging to enhance consumer safety.",
  },
];

const openQuestionResponsesWithThemes: Response[] = [
  {
    free_text: "",
    themes: ["A", "B", "C"],
  },
  {
    free_text:
      "I believe the current regulations should include clearer guidelines on the sourcing of ingredients to ensure ethical practices and sustainability.",
    themes: ["A", "C"],
  },
  {
    free_text:
      "The regulations could be improved by setting specific limits on sugar content to promote healthier options for consumers.",
    themes: ["B", "C"],
  },
  {
    free_text:
      "Consideration should be given to standardizing portion sizes to help consumers make informed choices and manage their calorie intake.",
    themes: ["C"],
  },
  {
    free_text:
      "It would be beneficial to include mandatory allergen warnings on all packaging to enhance consumer safety.",
    themes: [],
  },
];

export const openQuestion: Question = {
  text: "What are your thoughts on how the current chocolate bar regulations could be improved to better address consumer needs and industry standards?",
  number: 4,
  has_free_text: true,
  has_multiple_choice: false,
  responses: openQuestionResponses,
};

export const openQuestionWithThemes: Question = {
  ...openQuestion,
  ...{
    themes: openQuestionThemes,
    responses: openQuestionResponsesWithThemes,
  },
};

export const setupConsultation: Consultation = {
  title: "Dummy Consultation at Setup Stage",
  stage: "setup",
  users: [defaultUser.email],
  questions: [hybridQuestion, multChoiceQuestion, openQuestion],
};

export const analysisConsultation: Consultation = {
  title: "Dummy Consultation at Analysis Stage",
  stage: "analysis",
  users: [defaultUser.email],
  questions: [
    hybridQuestionWithThemes,
    multChoiceQuestion,
    openQuestionWithThemes,
  ],
};

export const signOffConsultation: Consultation = {
  title: "Dummy Consultation at Finalising Themes Stage",
  stage: "finalising_themes",
  users: [defaultUser.email],
  questions: [hybridQuestion, multChoiceQuestion, openQuestion],
};
