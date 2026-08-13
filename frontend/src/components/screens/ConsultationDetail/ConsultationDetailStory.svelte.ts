import ConsultationDetail from "./ConsultationDetail.svelte";
import {
  demoOptionsMock,
  defaultQuestionsMock,
  emptyQuestionsMock,
  longQuestionsMock,
  CONSULTATION_ID,
  defaultRespondentsMock,
} from "./mocks";

const consultationId = $state(CONSULTATION_ID);

export default {
  name: "ConsultationDetail",
  component: ConsultationDetail,
  category: "Screens",
  mocks: [defaultQuestionsMock, demoOptionsMock, defaultRespondentsMock],
  props: [{ name: "consultationId", value: consultationId, type: "text" }],
  stories: [
    {
      name: "No Questions",
      mocks: [emptyQuestionsMock, demoOptionsMock, defaultRespondentsMock],
      props: {
        consultationId: CONSULTATION_ID,
      },
    },
    {
      name: "Many Questions",
      mocks: [longQuestionsMock, demoOptionsMock, defaultRespondentsMock],
      props: {
        consultationId: CONSULTATION_ID,
      },
    },
  ],
};
