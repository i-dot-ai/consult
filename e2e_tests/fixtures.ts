type ConsultationStage = "setup" | "analysis" | "finalising_themes";

export type Theme = {
  name: string;
  description: string;
  key: string;
};

export type DemographicInfo = {
  age_group: string;
  nation: string;
}

export type Response = {
  free_text?: string;
  chosen_options?: string[];
  themes?: Theme["key"][];
  demographics?: DemographicInfo;
  evidence_rich?: boolean;
};

export type Question = {
  text: string;
  number: number;
  has_free_text: boolean;
  has_multiple_choice: boolean;
  multiple_choice_options?: string[];
  responses?: Response[];
  candidate_themes?: Theme[];
  themes?: Theme[];
  theme_status?: "draft" | "configured" | "finalising_themes" | "confirmed";
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
  email: "admin@example.com",
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
    demographics: { age_group: "18-35", nation: "England" },
  },
  {
    free_text:
      "Yes, I agree with the proposal as it will create a standardized framework that benefits both consumers and manufacturers.",
    chosen_options: [hybridQuestionOptions[0]],
    demographics: { age_group: "36-50", nation: "Wales" },
  },
  {
    free_text:
      "No, I do not agree because I feel the proposed categories are too restrictive and may stifle innovation in flavour development.",
    chosen_options: [hybridQuestionOptions[1]],
    demographics: { age_group: "51-65", nation: "Scotland" },
  },
  {
    free_text:
      "I agree with the proposal, but I think there should be room for additional categories to accommodate future trends.",
    chosen_options: [hybridQuestionOptions[0], hybridQuestionOptions[2]],
    demographics: { age_group: "18-35", nation: "Northern Ireland" },
  },
  {
    free_text:
      "I disagree with the proposal as it does not sufficiently account for regional flavour preferences across the UK.",
    chosen_options: [hybridQuestionOptions[1]],
    demographics: { age_group: "36-50", nation: "England" },
  },
];

const hybridQuestionResponsesWithThemes: Response[] = [
  {
    free_text:
      "Yes, I strongly support this proposal as it provides a clear standardized framework while also encouraging innovation in the chocolate industry.",
    chosen_options: [hybridQuestionOptions[0]],
    themes: ["A", "B"],
    evidence_rich: true,
    demographics: { age_group: "18-35", nation: "England" },
  },
  {
    free_text:
      "Yes, I agree with the proposal as it will create a standardized framework that benefits both consumers and manufacturers.",
    chosen_options: [hybridQuestionOptions[0]],
    themes: ["A"],
    demographics: { age_group: "36-50", nation: "Wales" },
  },
  {
    free_text:
      "No, I do not agree because I feel the proposed categories are too restrictive and may stifle innovation in flavour development.",
    chosen_options: [hybridQuestionOptions[1]],
    themes: ["B"],
    demographics: { age_group: "51-65", nation: "Scotland" },
  },
  {
    free_text:
      "I agree with the proposal, but I think there should be room for additional categories to accommodate future trends.",
    chosen_options: [hybridQuestionOptions[0], hybridQuestionOptions[2]],
    themes: [],
    demographics: { age_group: "18-35", nation: "Northern Ireland" },
  },
  {
    free_text:
      "I disagree with the proposal as it does not sufficiently account for regional flavour preferences across the UK.",
    chosen_options: [hybridQuestionOptions[1]],
    themes: ["A"],
    demographics: { age_group: "36-50", nation: "England" },
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
    demographics: { age_group: "18-35", nation: "England" },
  },
  {
    free_text:
      "I believe the current regulations should include clearer guidelines on the sourcing of ingredients to ensure ethical practices and sustainability.",
    demographics: { age_group: "36-50", nation: "Wales" },
  },
  {
    free_text:
      "The regulations could be improved by setting specific limits on sugar content to promote healthier options for consumers.",
    demographics: { age_group: "51-65", nation: "Scotland" },
  },
  {
    free_text:
      "Consideration should be given to standardizing portion sizes to help consumers make informed choices and manage their calorie intake.",
    demographics: { age_group: "18-35", nation: "Northern Ireland" },
  },
  {
    free_text:
      "It would be beneficial to include mandatory allergen warnings on all packaging to enhance consumer safety.",
    demographics: { age_group: "36-50", nation: "England" },
  },
];

const openQuestionResponsesWithThemes: Response[] = [
  {
    free_text:
      "The regulations should focus on innovative approaches to packaging, exploring new flavor combinations while maintaining ethical sourcing standards.",
    themes: ["A", "B", "C"],
    demographics: { age_group: "18-35", nation: "England" },
  },
  {
    free_text:
      "I believe the current regulations should include clearer guidelines on the sourcing of ingredients to ensure ethical practices and sustainability.",
    themes: ["A", "C"],
    demographics: { age_group: "36-50", nation: "Wales" },
  },
  {
    free_text:
      "The regulations could be improved by setting specific limits on sugar content to promote healthier options for consumers.",
    themes: ["B", "C"],
    demographics: { age_group: "51-65", nation: "Scotland" },
  },
  {
    free_text:
      "Consideration should be given to standardizing portion sizes to help consumers make informed choices and manage their calorie intake.",
    themes: ["C"],
    demographics: { age_group: "18-35", nation: "Northern Ireland" },
  },
  {
    free_text:
      "It would be beneficial to include mandatory allergen warnings on all packaging to enhance consumer safety.",
    themes: [],
    demographics: { age_group: "36-50", nation: "England" },
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
  title: "Test Consultation at Setup Stage",
  stage: "setup",
  users: [defaultUser.email],
  questions: [hybridQuestion, multChoiceQuestion, openQuestion],
};

export const finalisingThemesConsultation: Consultation = {
  title: "Dummy Consultation at Finalising Themes Stage (with Candidate Themes)",
  stage: "finalising_themes",
  users: [defaultUser.email],
  questions: [
    {
      ...hybridQuestion,
      candidate_themes: hybridQuestionThemes,
    },
    multChoiceQuestion,
    {
      ...openQuestion,
      candidate_themes: openQuestionThemes,
    },
  ],
};

export const analysisConsultation: Consultation = {
  title: "Test Consultation at Analysis Stage",
  stage: "analysis",
  users: [defaultUser.email],
  questions: [
    hybridQuestionWithThemes,
    multChoiceQuestion,
    openQuestionWithThemes,
  ],
};

// NOTE: signOffConsultation is nearly identical to finalisingThemesConsultation
// The only difference is the title - both are used by different test suites
// that were created at different times. Consider consolidating in the future.
export const signOffConsultation: Consultation = {
  title: "Test Consultation at Finalising Themes Stage",
  stage: "finalising_themes",
  users: [defaultUser.email],
  questions: [
    {
      ...hybridQuestion,
      candidate_themes: hybridQuestionThemes,
    },
    multChoiceQuestion,
    {
      ...openQuestion,
      candidate_themes: openQuestionThemes,
    },
  ],
};

// signedOffConsultation represents a consultation in the analysis stage
// with themes that have been finalized (theme_status="confirmed")
// Use this fixture to test the completed/signed-off themes view

const signedOffTheme1: Theme[] = [
  {
    name: "Quality Standards",
    description: "Comments about maintaining high quality standards in chocolate production",
    key: "A",
  },
  {
    name: "Consumer Protection",
    description: "Responses focused on protecting consumer interests",
    key: "B",
  },
];

const signedOffResponses1: Response[] = [
  {
    free_text: "The proposed standards will ensure consistent quality across all chocolate products.",
    chosen_options: ["Yes"],
    themes: ["A"],
    demographics: { age_group: "36-50", nation: "England" },
  },
  {
    free_text: "This regulation prioritizes consumer safety which is essential for public health.",
    chosen_options: ["Yes"],
    themes: ["B"],
    demographics: { age_group: "51-65", nation: "Wales" },
  },
  {
    free_text: "Both quality standards and consumer protection are important considerations in this regulation.",
    chosen_options: ["Yes"],
    themes: ["A", "B"],
    evidence_rich: true,
    demographics: { age_group: "18-35", nation: "Scotland" },
  },
];

const signedOffQuestion1: Question = {
  text: "Do you support the proposed chocolate quality standards regulation?",
  number: 1,
  has_free_text: true,
  has_multiple_choice: true,
  multiple_choice_options: ["Yes", "No", "Don't know"],
  responses: signedOffResponses1,
  themes: signedOffTheme1,
  theme_status: "confirmed",
};

const signedOffTheme2: Theme[] = [
  {
    name: "Industry Impact",
    description: "Discussion of how regulations affect chocolate manufacturers",
    key: "A",
  },
  {
    name: "Market Competition",
    description: "Concerns about competitive dynamics in the chocolate industry",
    key: "B",
  },
];

const signedOffResponses2: Response[] = [
  {
    free_text: "Small manufacturers may struggle to meet these new regulatory requirements and costs.",
    chosen_options: ["No"],
    themes: ["A"],
    demographics: { age_group: "36-50", nation: "Northern Ireland" },
  },
  {
    free_text: "Large companies will benefit from these regulations while smaller competitors are pushed out.",
    chosen_options: ["No"],
    themes: ["B"],
    evidence_rich: true,
    demographics: { age_group: "51-65", nation: "England" },
  },
  {
    free_text: "The industry impact assessment shows significant effects on both production costs and market dynamics.",
    chosen_options: ["Don't know"],
    themes: ["A", "B"],
    demographics: { age_group: "18-35", nation: "Wales" },
  },
];

const signedOffQuestion2: Question = {
  text: "What are your views on the economic impact of the proposed chocolate regulations?",
  number: 2,
  has_free_text: true,
  has_multiple_choice: true,
  multiple_choice_options: ["Positive impact", "Negative impact", "Neutral", "Don't know"],
  responses: signedOffResponses2,
  themes: signedOffTheme2,
  theme_status: "confirmed",
};

const signedOffTheme3: Theme[] = [
  {
    name: "Implementation Timeline",
    description: "Feedback on proposed timeline and implementation phases",
    key: "A",
  },
  {
    name: "Compliance Costs",
    description: "Economic burden and financial impact on businesses",
    key: "B",
  },
  {
    name: "Regional Variations",
    description: "Need for regional adaptation and flexibility",
    key: "C",
  },
];

const signedOffResponses3: Response[] = [
  {
    free_text: "The 12-month implementation period is too short for businesses to adapt their processes adequately.",
    chosen_options: ["Disagree"],
    themes: ["A"],
    demographics: { age_group: "36-50", nation: "Scotland" },
  },
  {
    free_text: "Compliance costs will be substantial, particularly for updating equipment and training staff on new standards.",
    chosen_options: ["Disagree"],
    themes: ["B"],
    evidence_rich: true,
    demographics: { age_group: "51-65", nation: "England" },
  },
  {
    free_text: "Different regions have unique chocolate-making traditions that should be accommodated in the regulations.",
    chosen_options: ["Agree"],
    themes: ["C"],
    demographics: { age_group: "18-35", nation: "Northern Ireland" },
  },
  {
    free_text: "The timeline is unrealistic given the costs involved, and regional differences must be considered.",
    chosen_options: ["Disagree"],
    themes: ["A", "B", "C"],
    evidence_rich: true,
    demographics: { age_group: "36-50", nation: "Wales" },
  },
];

const signedOffQuestion3: Question = {
  text: "Do you agree with the proposed implementation approach for the chocolate regulations?",
  number: 3,
  has_free_text: true,
  has_multiple_choice: true,
  multiple_choice_options: ["Strongly agree", "Agree", "Disagree", "Strongly disagree"],
  responses: signedOffResponses3,
  themes: signedOffTheme3,
  theme_status: "confirmed",
};

export const signedOffConsultation: Consultation = {
  title: "Test Consultation with Signed Off Themes",
  stage: "analysis",
  users: [defaultUser.email],
  questions: [
    signedOffQuestion1,
    signedOffQuestion2,
    signedOffQuestion3,
  ],
};
