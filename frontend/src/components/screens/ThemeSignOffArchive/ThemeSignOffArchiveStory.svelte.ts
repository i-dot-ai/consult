import { getApiQuestionsUrl } from "../../../global/routes";
import { createFetchMock } from "../../../global/utils";
import testData from "./testData";

import ThemeSignOffArchive from "./ThemeSignOffArchive.svelte";

let consultationId = $state("test-consultation");

const noQuestionStoryFetch = createFetchMock([{
  matcher: getApiQuestionsUrl("test-consultation"),
  response: { ...testData, results: [] },
}]);

const interactiveStoryFetch = createFetchMock([{
  matcher: getApiQuestionsUrl("test-consultation"),
  response: testData,
}]);

const allSignedOffStoryFetch = createFetchMock([{
  matcher: getApiQuestionsUrl("test-consultation"),
  response: {
    ...testData,
    results: testData.results.map(question => ({...question, "theme_status": "confirmed"})),
  },
}]);

export default {
  name: "ThemeSignOffArchive",
  component: ThemeSignOffArchive,
  category: "Theme Sign Off",
  props: [
    { name: "consultationId", value: consultationId, type: "text" },
    { name: "mockFetch", value: interactiveStoryFetch.fetch, type: "func" },
  ],
  stories: [
    {
      name: "No Questions",
      props: {
        consultationId: "test-consultation",
        mockFetch: noQuestionStoryFetch.fetch,
      },
    },
    {
      name: "All Questions Signed Off",
      props: {
        consultationId: "test-consultation",
        mockFetch: allSignedOffStoryFetch.fetch,
      },
    },
  ],
};
