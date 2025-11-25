import { getApiConsultationUrl, getApiQuestionsUrl } from "../../../global/routes";
import { createFetchMock } from "../../../global/utils";

import testData from "./testData";

import ThemeSignOffArchive from "./ThemeSignOffArchive.svelte";

let consultationId = $state("test-consultation");

const mocks = {
  interactive: {
    questions: createFetchMock([{
      matcher: getApiQuestionsUrl("test-consultation"),
      response: testData,
    }]),
    consultation: createFetchMock([{
      matcher: getApiConsultationUrl("test-consultation"),
      response: { stage: "theme_sign_off" },
    }]),
    consultationUpdate: createFetchMock(
      [{
        matcher: getApiConsultationUrl("test-consultation"),
        response: testData,
      }],
      (args) => alert(`Update Called With: ${args.options.body}`)
    ),
  },

  noQuestions: {
    questions: createFetchMock([{
      matcher: getApiQuestionsUrl("test-consultation"),
      response: { ...testData, results: [] },
    }]),
    consultation: createFetchMock([{
      matcher: getApiConsultationUrl("test-consultation"),
      response: { stage: "theme_sign_off" },
    }]),
    consultationUpdate: createFetchMock(
      [{
        matcher: getApiConsultationUrl("test-consultation"),
        response: testData,
      }],
    ),
  },

  allSignedOff: {
    questions: createFetchMock([{
      matcher: getApiQuestionsUrl("test-consultation"),
      response: {
        ...testData,
        results: testData.results.map(question => ({...question, "theme_status": "confirmed"})),
      },
    }]),
    consultation: createFetchMock([{
      matcher: getApiConsultationUrl("test-consultation"),
      response: { stage: "theme_sign_off" },
    }]),
    consultationUpdate: createFetchMock(
      [{
        matcher: getApiConsultationUrl("test-consultation"),
        response: testData,
      }],
      ({ options }) => alert(`Update Called With: ${options.body}`)
    ),
  },
}

export default {
  name: "ThemeSignOffArchive",
  component: ThemeSignOffArchive,
  category: "Theme Sign Off",
  props: [
    { name: "consultationId", value: consultationId, type: "text" },
    { name: "questionsFetch", value: mocks.interactive.questions.fetch, type: "func" },
    { name: "consultationFetch", value: mocks.interactive.consultation.fetch, type: "func" },
    { name: "consultationUpdateFetch", value: mocks.interactive.consultationUpdate.fetch, type: "func" },
  ],
  stories: [
    {
      name: "No Questions",
      props: {
        consultationId: "test-consultation",
        questionsFetch: mocks.noQuestions.questions.fetch,
        consultationFetch: mocks.noQuestions.consultation.fetch,
        consultationUpdateFetch: mocks.noQuestions.consultationUpdate.fetch,
      },
    },
    {
      name: "All Questions Signed Off",
      props: {
        consultationId: "test-consultation",
        questionsFetch: mocks.allSignedOff.questions.fetch,
        consultationFetch: mocks.allSignedOff.consultation.fetch,
        consultationUpdateFetch: mocks.allSignedOff.consultationUpdate.fetch,
      },
    },
  ],
};
