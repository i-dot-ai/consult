import ConsultationView from "./ConsultationView.svelte";
import { CONSULTATION_ID, defaultMock, knownUserMock, multipleUsersMock, sameUserMock, userMock } from "./mocks";

const consultationId = $state(CONSULTATION_ID);

export default {
  name: "ConsultationView",
  component: ConsultationView,
  category: "Screens",
  props: [{ name: "consultationId", value: consultationId, type: "text" }],
  mocks: [defaultMock, userMock],
  stories: [
    {
        name: "Multiple Users",
        mocks: [multipleUsersMock, userMock],
        props: {consultationId},
    },
    {
        name: "Same User",
        mocks: [sameUserMock, userMock],
        props: {consultationId},
    },
    {
        name: "Known User",
        mocks: [knownUserMock, userMock],
        props: {consultationId},
    },
  ],
};
