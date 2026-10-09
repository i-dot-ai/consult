import ConsultationView from "./ConsultationView.svelte";
import { CONSULTATION_ID, defaultMock, knownUserMock, multipleUsersMock, sameUserMock, stageAssigningThemesMock, stageFinaliseThemesMock, stageFindingThemesMock, stageSetupMock, userMock, userNotStaffMock } from "./mocks";

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
    {
        name: "Stage - Finalising Themes",
        mocks: [userMock, stageFinaliseThemesMock],
        props: {consultationId},
    },
    {
        name: "Stage - Data Setup",
        mocks: [userMock, stageSetupMock],
        props: {consultationId},
    },
    {
        name: "Stage - Assigning Themes",
        mocks: [userMock, stageAssigningThemesMock],
        props: {consultationId},
    },
    {
        name: "Stage - Finding Themes",
        mocks: [userMock, stageFindingThemesMock],
        props: {consultationId},
    },
    {
        name: "User Not Staff",
        mocks: [defaultMock, userNotStaffMock],
        props: {consultationId},
    },
  ],
};
