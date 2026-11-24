import {
  getApiAnswersUrl,
  getApiConsultationRespondentsUrl,
  getApiConsultationRespondentUrl,
  getApiQuestionsUrl,
  getQuestionsByRespondentUrl,
} from "../../../global/routes";

export const CONSULTATION_ID = "test-consultation";
export const QUESTION_ID = "test-question";
export const RESPONDENT_ID = "test-respondent";

let stakeholderName: string | null = null;

export const consultationQuestionsMock = {
  url: getApiQuestionsUrl(CONSULTATION_ID),
  body: {
    count: 4,
    next: null,
    previous: null,
    results: [
      {
        id: "5e8176da-fdcd-4f55-ab7b-b2ca8a12a467",
        number: 1,
        total_response_count: 100,
        free_text_response_count: 100,
        multi_choice_response_count: 0,
        question_text:
          "Do you agree with the proposal to align the flavour categories of chocolate bars as outlined in the draft guidelines of the Chocolate Bar Regulation for the United Kingdom?",
        has_free_text: true,
        has_multiple_choice: true,
        multiple_choice_answer: [
          {
            text: "Yes",
            response_count: 99,
          },
          {
            text: "No",
            response_count: 18,
          },
          {
            text: "Don't know",
            response_count: 98,
          },
          {
            text: "No answer",
            response_count: 17,
          },
        ],
        proportion_of_audited_answers: 0,
        theme_status: "draft",
      },
      {
        id: "ef855675-af2b-4cfe-871d-ad108360e57a",
        number: 2,
        total_response_count: 100,
        free_text_response_count: 100,
        multi_choice_response_count: 0,
        question_text:
          "Do you agree with the proposal to align the flavour categories of chocolate bars as outlined in the draft guidelines of the Chocolate Bar Regulation for the United Kingdom?",
        has_free_text: false,
        has_multiple_choice: true,
        multiple_choice_answer: [
          {
            text: "Yes",
            response_count: 58,
          },
          {
            text: "No",
            response_count: 61,
          },
          {
            text: "Don't know",
            response_count: 58,
          },
          {
            text: "No answer",
            response_count: 64,
          },
        ],
        proportion_of_audited_answers: 0,
        theme_status: "draft",
      },
      {
        id: "92848794-2072-41c4-b3bf-78248a6995da",
        number: 3,
        total_response_count: 100,
        free_text_response_count: 100,
        multi_choice_response_count: 0,
        question_text:
          "Which of the following factors do you believe are important when considering the packaging of chocolate bars? Please select all that apply: a) Sustainability, b) Design, c) Cost-effectiveness, d) Durability, e) Brand recognition.",
        has_free_text: false,
        has_multiple_choice: true,
        multiple_choice_answer: [
          {
            text: "Sustainability",
            response_count: 63,
          },
          {
            text: "Design",
            response_count: 62,
          },
          {
            text: "Cost-effectiveness",
            response_count: 63,
          },
          {
            text: "Durability",
            response_count: 66,
          },
          {
            text: "Brand recognition",
            response_count: 56,
          },
        ],
        proportion_of_audited_answers: 0,
        theme_status: "draft",
      },
      {
        id: "b20f35ee-411b-4746-9029-1e9b02610dea",
        number: 4,
        total_response_count: 100,
        free_text_response_count: 100,
        multi_choice_response_count: 0,
        question_text:
          "What are your thoughts on how the current chocolate bar regulations could be improved to better address consumer needs and industry standards?",
        has_free_text: true,
        has_multiple_choice: false,
        multiple_choice_answer: [],
        proportion_of_audited_answers: 0,
        theme_status: "draft",
      },
    ],
  },
};

export const respondentsMock = {
  url: "path:" + getApiConsultationRespondentsUrl(CONSULTATION_ID),
  body: () => ({
    count: 3,
    next: null,
    previous: null,
    results: [
      {
        id: "7a2d12a8-9b51-4b06-9d72-4b225a335764",
        themefinder_id: 3,
        demographics: [],
        name: null,
      },
      {
        id: "d34547db-21b8-4586-905a-f71f6090e466",
        themefinder_id: 2,
        demographics: [],
        name: null,
      },
      {
        id: RESPONDENT_ID,
        themefinder_id: 1,
        demographics: [
          {
            id: "d835f431-a1d2-4754-b744-0f61f6252348",
            name: "Test Demo",
            value: "Test demo value",
          },
        ],
        name: stakeholderName,
      },
    ],
  }),
};
export const responsesMock = {
  url: "path:" + getApiAnswersUrl(CONSULTATION_ID),
  body: {
    total_count: 4,
    has_more_pages: false,
    next_cursor: null,
    all_respondents: [
      {
        id: "a97ee5ee-f23e-4ff4-b9c8-a32982332501",
        identifier: "2",
        respondent_id: "d34547db-21b8-4586-905a-f71f6090e466",
        respondent: {
          id: "d34547db-21b8-4586-905a-f71f6090e466",
          themefinder_id: 2,
          demographics: [],
          name: null,
        },
        question_id: "5e8176da-fdcd-4f55-ab7b-b2ca8a12a467",
        free_text_answer_text: "",
        demographic_data: {},
        themes: [],
        multiple_choice_answer: ["Yes"],
        evidenceRich: null,
        sentiment: null,
        human_reviewed: null,
        is_flagged: false,
        is_edited: false,
        is_read: false,
      },
      {
        id: "2bfda55e-4a27-4456-8dfb-6dc1ca1a6619",
        identifier: "2",
        respondent_id: "d34547db-21b8-4586-905a-f71f6090e466",
        respondent: {
          id: "d34547db-21b8-4586-905a-f71f6090e466",
          themefinder_id: 2,
          demographics: [],
          name: null,
        },
        question_id: "ef855675-af2b-4cfe-871d-ad108360e57a",
        free_text_answer_text: null,
        demographic_data: {},
        themes: [],
        multiple_choice_answer: ["No"],
        evidenceRich: null,
        sentiment: null,
        human_reviewed: null,
        is_flagged: false,
        is_edited: false,
        is_read: false,
      },
      {
        id: "08225ef9-83ad-46ee-aca5-937e605635af",
        identifier: "2",
        respondent_id: "d34547db-21b8-4586-905a-f71f6090e466",
        respondent: {
          id: "d34547db-21b8-4586-905a-f71f6090e466",
          themefinder_id: 2,
          demographics: [],
          name: null,
        },
        question_id: "92848794-2072-41c4-b3bf-78248a6995da",
        free_text_answer_text: null,
        demographic_data: {},
        themes: [],
        multiple_choice_answer: [
          "Brand recognition",
          "Design",
          "Cost-effectiveness",
        ],
        evidenceRich: null,
        sentiment: null,
        human_reviewed: null,
        is_flagged: false,
        is_edited: false,
        is_read: false,
      },
      {
        id: "c28de2d4-8cc6-4861-add5-676bcdfb8d94",
        identifier: "2",
        respondent_id: "d34547db-21b8-4586-905a-f71f6090e466",
        respondent: {
          id: "d34547db-21b8-4586-905a-f71f6090e466",
          themefinder_id: 2,
          demographics: [],
          name: null,
        },
        question_id: "b20f35ee-411b-4746-9029-1e9b02610dea",
        free_text_answer_text:
          "It would be beneficial to include mandatory allergen warnings on all packaging to enhance consumer safety.",
        demographic_data: {},
        themes: [],
        multiple_choice_answer: [],
        evidenceRich: null,
        sentiment: null,
        human_reviewed: null,
        is_flagged: false,
        is_edited: false,
        is_read: false,
      },
    ],
  },
};

export const questionsMock = {
  url: getQuestionsByRespondentUrl(CONSULTATION_ID, RESPONDENT_ID),
  body: {
    count: 4,
    next: null,
    previous: null,
    results: [
      {
        id: "5e8176da-fdcd-4f55-ab7b-b2ca8a12a467",
        number: 1,
        total_response_count: 100,
        free_text_response_count: 100,
        multi_choice_response_count: 0,
        question_text:
          "Do you agree with the proposal to align the flavour categories of chocolate bars as outlined in the draft guidelines of the Chocolate Bar Regulation for the United Kingdom?",
        has_free_text: true,
        has_multiple_choice: true,
        multiple_choice_answer: [
          {
            text: "Yes",
            response_count: 99,
          },
          {
            text: "No",
            response_count: 18,
          },
          {
            text: "Don't know",
            response_count: 98,
          },
          {
            text: "No answer",
            response_count: 17,
          },
        ],
        proportion_of_audited_answers: 0,
        theme_status: "draft",
      },
      {
        id: "ef855675-af2b-4cfe-871d-ad108360e57a",
        number: 2,
        total_response_count: 100,
        free_text_response_count: 100,
        multi_choice_response_count: 0,
        question_text:
          "Do you agree with the proposal to align the flavour categories of chocolate bars as outlined in the draft guidelines of the Chocolate Bar Regulation for the United Kingdom?",
        has_free_text: false,
        has_multiple_choice: true,
        multiple_choice_answer: [
          {
            text: "Yes",
            response_count: 58,
          },
          {
            text: "No",
            response_count: 61,
          },
          {
            text: "Don't know",
            response_count: 58,
          },
          {
            text: "No answer",
            response_count: 64,
          },
        ],
        proportion_of_audited_answers: 0,
        theme_status: "draft",
      },
      {
        id: "92848794-2072-41c4-b3bf-78248a6995da",
        number: 3,
        total_response_count: 100,
        free_text_response_count: 100,
        multi_choice_response_count: 0,
        question_text:
          "Which of the following factors do you believe are important when considering the packaging of chocolate bars? Please select all that apply: a) Sustainability, b) Design, c) Cost-effectiveness, d) Durability, e) Brand recognition.",
        has_free_text: false,
        has_multiple_choice: true,
        multiple_choice_answer: [
          {
            text: "Sustainability",
            response_count: 63,
          },
          {
            text: "Design",
            response_count: 62,
          },
          {
            text: "Cost-effectiveness",
            response_count: 63,
          },
          {
            text: "Durability",
            response_count: 66,
          },
          {
            text: "Brand recognition",
            response_count: 56,
          },
        ],
        proportion_of_audited_answers: 0,
        theme_status: "draft",
      },
      {
        id: "b20f35ee-411b-4746-9029-1e9b02610dea",
        number: 4,
        total_response_count: 100,
        free_text_response_count: 100,
        multi_choice_response_count: 0,
        question_text:
          "What are your thoughts on how the current chocolate bar regulations could be improved to better address consumer needs and industry standards?",
        has_free_text: true,
        has_multiple_choice: false,
        multiple_choice_answer: [],
        proportion_of_audited_answers: 0,
        theme_status: "draft",
      },
    ],
  },
};

export const updateRespondentMock = {
  url: getApiConsultationRespondentUrl(CONSULTATION_ID, RESPONDENT_ID),
  method: "PATCH",
  body: ({ body }: { body: string }) => {
    stakeholderName = JSON.parse(body).name;
  },
};
