import ConsultationView from "./ConsultationView.svelte";
import { CONSULTATION_ID, defaultMock, knownUserMock, multipleUsersMock, sameUserMock, stageFinaliseThemesMock, userMock } from "./mocks";

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
        mocks: [sameUserMock, defaultMock],
        props: {consultationId},
    },
    {
        name: "Known User",
        mocks: [knownUserMock, defaultMock],
        props: {consultationId},
    },
    {
        name: "Stage - Finalising Themes",
        mocks: [userMock, stageFinaliseThemesMock],
        props: {consultationId},
    },
  ],
};
