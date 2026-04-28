import { getApiConsultationUrl, getApiDemographicsUrl, getApiQuestionResponsesUrl, getApiQuestionThemesUrl, getApiQuestionUrl, updateResponseReadStatus } from "../../../global/routes";
import { paginateArray } from "../../../global/utils";

export const CONSULTATION_ID = "test-consultation";
export const QUESTION_ID = "test-question";

let answers = [
  {
    "id": "f3f8f938-281b-4b74-ac80-6db7390e2171",
    "identifier": "1",
    "respondent_id": "ab299432-7f39-4360-bf85-f0f374dd1f34",
    "respondent": {
        "id": "ab299432-7f39-4360-bf85-f0f374dd1f34",
        "themefinder_id": 1,
        "demographics": [],
        "name": null
    },
    "question_id": "5e8176da-fdcd-4f55-ab7b-b2ca8a12a467",
    "free_text_answer_text": "I support the proposal because it will likely improve transparency and consistency in labelling for consumers.",
    "demographic_data": {},
    "themes": [],
    "multiple_choice_answer": [
        "No"
    ],
    "evidenceRich": null,
    "sentiment": null,
    "human_reviewed": null,
    "is_flagged": false,
    "is_edited": false,
    "is_read": false
  },
  {
    "id": "a97ee5ee-f23e-4ff4-b9c8-a32982332501",
    "identifier": "2",
    "respondent_id": "d34547db-21b8-4586-905a-f71f6090e466",
    "respondent": {
        "id": "d34547db-21b8-4586-905a-f71f6090e466",
        "themefinder_id": 2,
        "demographics": [],
        "name": null
    },
    "question_id": "5e8176da-fdcd-4f55-ab7b-b2ca8a12a467",
    "free_text_answer_text": "",
    "demographic_data": {},
    "themes": [],
    "multiple_choice_answer": [
        "Yes"
    ],
    "evidenceRich": null,
    "sentiment": null,
    "human_reviewed": null,
    "is_flagged": false,
    "is_edited": false,
    "is_read": false
  },
  {
    "id": "918d1801-13d4-4008-8e2a-5419927aa21f",
    "identifier": "3",
    "respondent_id": "7a2d12a8-9b51-4b06-9d72-4b225a335764",
    "respondent": {
        "id": "7a2d12a8-9b51-4b06-9d72-4b225a335764",
        "themefinder_id": 3,
        "demographics": [],
        "name": null
    },
    "question_id": "5e8176da-fdcd-4f55-ab7b-b2ca8a12a467",
    "free_text_answer_text": "Yes, I agree with the proposal as it will create a standardized framework that benefits both consumers and manufacturers.",
    "demographic_data": {},
    "themes": [],
    "multiple_choice_answer": [
        "Don't know",
        "Yes"
    ],
    "evidenceRich": null,
    "sentiment": null,
    "human_reviewed": null,
    "is_flagged": false,
    "is_edited": false,
    "is_read": false
  },
  {
    "id": "fd6885d6-6a89-442c-afe4-a4c3b2f9ffa7",
    "identifier": "4",
    "respondent_id": "4f9253bf-cd6a-4e1e-8620-825045125cdc",
    "respondent": {
        "id": "4f9253bf-cd6a-4e1e-8620-825045125cdc",
        "themefinder_id": 4,
        "demographics": [],
        "name": null
    },
    "question_id": "5e8176da-fdcd-4f55-ab7b-b2ca8a12a467",
    "free_text_answer_text": "I disagree with the proposal as it does not sufficiently account for regional flavour preferences across the UK.",
    "demographic_data": {},
    "themes": [],
    "multiple_choice_answer": [
        "No answer",
        "No",
        "Don't know",
        "Yes"
    ],
    "evidenceRich": null,
    "sentiment": null,
    "human_reviewed": null,
    "is_flagged": false,
    "is_edited": false,
    "is_read": false
  },
  {
    "id": "d6a95f98-5adf-4587-8299-6e2d85851e72",
    "identifier": "5",
    "respondent_id": "c737bce1-3f30-4be7-aacc-391169300e03",
    "respondent": {
        "id": "c737bce1-3f30-4be7-aacc-391169300e03",
        "themefinder_id": 5,
        "demographics": [],
        "name": null
    },
    "question_id": "5e8176da-fdcd-4f55-ab7b-b2ca8a12a467",
    "free_text_answer_text": "",
    "demographic_data": {},
    "themes": [],
    "multiple_choice_answer": [
        "Don't know",
        "Yes"
    ],
    "evidenceRich": null,
    "sentiment": null,
    "human_reviewed": null,
    "is_flagged": false,
    "is_edited": false,
    "is_read": false
  }
];

const filterAnswers = (answers: any[], params: any) => {
  let pages = paginateArray(answers, Number.parseInt(params.page_size));
  let intendedPage = Number.parseInt(params.page);

  let result = intendedPage > pages.length
    ? []
    : pages[intendedPage - 1];

  if (params.searchValue) {
    result = result.filter(item => (
      item.free_text_answer_text.toLocaleLowerCase().includes(params.searchValue.toLocaleLowerCase())
    ))
  }

  return result;
}

export const consultationMock = {
  url: getApiConsultationUrl(CONSULTATION_ID),
  body: {
    "id": "4d1414d5-9300-447b-b788-50d0bef7e807",
    "title": "Dummy Consultation at Theme Sign Off Stage",
    "code": "",
    "stage": "theme_sign_off",
    "users": [
        {
            "id": 1,
            "email": "email@example.com",
            "is_staff": true,
            "created_at": "2026-01-29T14:15:50.850685Z"
        }
    ],
    "created_at": "2026-01-29T14:23:12.423686Z",
  },
}

export const questionMock = {
  url: getApiQuestionUrl(CONSULTATION_ID, QUESTION_ID),
  body: {
    "id": "5e8176da-fdcd-4f55-ab7b-b2ca8a12a467",
    "number": 1,
    "total_responses": 100,
    "question_text": "Do you agree with the proposal to align the flavour categories of chocolate bars as outlined in the draft guidelines of the Chocolate Bar Regulation for the United Kingdom?",
    "has_free_text": true,
    "has_multiple_choice": true,
    "multiple_choice_answer": [
        {
            "id": "c0dd6e81-9503-4156-bf9e-548efd975cf8",
            "text": "Yes",
            "response_count": 99
        },
        {
            "id": "7448a8bd-fb8a-464f-a07b-7250299daa26",
            "text": "No",
            "response_count": 18
        },
        {
            "id": "7adf9e67-86ee-4848-8c1b-8a668c0f6c3c",
            "text": "Don't know",
            "response_count": 98
        },
        {
            "id": "171f1142-d62f-4f70-aeb0-1fe738ad4789",
            "text": "No answer",
            "response_count": 17
        }
    ],
    "proportion_of_audited_answers": 0,
    "theme_status": "draft",
  }
}

export const themesMock = {
  url: "path:" + getApiQuestionThemesUrl(CONSULTATION_ID, QUESTION_ID),
  body: {
    "themes": [
        {
            "id": "26656d42-9b12-413f-bef8-1879d04f0d98",
            "name": "Standardized framework",
            "description": "A standardized framework that benefits both consumers and manufacturers.",
            "count": 0
        }
    ]
  }
}

export const answersMock = {
  url: "path:" + getApiQuestionResponsesUrl(CONSULTATION_ID, QUESTION_ID),
  body: ({ url }: { url: string }) => {
    const queryParams = Object.fromEntries(new URLSearchParams(url.split("?")[1]));

    const filteredAnswers = filterAnswers(answers, queryParams);
    
    return {
      "respondents_total": filteredAnswers.length,
      "filtered_total": filteredAnswers.length,
      "has_more_pages": true,
      "all_respondents": filteredAnswers,
    }
  }
}

export const demoMock = {
  url: getApiDemographicsUrl(CONSULTATION_ID),
  body: [],
}

export const answerUpdateMock = {
  regexp: "*host" + updateResponseReadStatus(CONSULTATION_ID, ":answerId"),
  method: "POST",
}