import ConsultationDetail from "./ConsultationDetail.svelte";
import { demoOptionsMock, defaultQuestionsMock, emptyQuestionsMock, longQuestionsMock } from "./mocks";

const consultationId = $state("test-consultation");

export default {
  name: "ConsultationDetail",
  component: ConsultationDetail,
  category: "Screens",
  mocks: [
    defaultQuestionsMock,
    demoOptionsMock,
  ],
  props: [
    { name: "consultationId", value: consultationId, type: "text" },
  ],
  stories: [
    {
      name: "No Questions",
      mocks: [
        emptyQuestionsMock,
        demoOptionsMock,
      ],
      props: {
        consultationId: "test-consultation",
      }
    },
    {
      name: "Many Questions",
      mocks: [
        longQuestionsMock,
        demoOptionsMock,
      ],
      props: {
        consultationId: "test-consultation",
      }
    },
  ],
};
