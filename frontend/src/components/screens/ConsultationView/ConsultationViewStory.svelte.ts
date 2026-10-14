import ConsultationView from "./ConsultationView.svelte";
import {
  CONSULTATION_ID,
  defaultMock,
  knownUserMock,
  multipleUsersMock,
  renameErrorMock,
  renameMock,
  renameThrowsMock,
  sameUserMock,
  stageAssigningThemesMock,
  stageFinaliseThemesMock,
  stageFindingThemesMock,
  stageSetupMock,
  userMock,
  userNotStaffMock,
} from "./mocks";

const consultationId = $state(CONSULTATION_ID);

export default {
  name: "ConsultationView",
  component: ConsultationView,
  category: "Screens",
  props: [{ name: "consultationId", value: consultationId, type: "text" }],
  mocks: [defaultMock, userMock, renameMock],
  stories: [
    {
      name: "Multiple Users",
      mocks: [multipleUsersMock, userMock, renameMock],
      props: { consultationId },
    },
    {
      name: "Same User",
      mocks: [sameUserMock, userMock, renameMock],
      props: { consultationId },
    },
    {
      name: "Known User",
      mocks: [knownUserMock, userMock, renameMock],
      props: { consultationId },
    },
    {
      name: "Stage - Finalising Themes",
      mocks: [userMock, stageFinaliseThemesMock, renameMock],
      props: { consultationId },
    },
    {
      name: "Stage - Data Setup",
      mocks: [userMock, stageSetupMock, renameMock],
      props: { consultationId },
    },
    {
      name: "Stage - Assigning Themes",
      mocks: [userMock, stageAssigningThemesMock, renameMock],
      props: { consultationId },
    },
    {
      name: "Stage - Finding Themes",
      mocks: [userMock, stageFindingThemesMock, renameMock],
      props: { consultationId },
    },
    {
      name: "User Not Staff",
      mocks: [defaultMock, userNotStaffMock, renameMock],
      props: { consultationId },
    },
    {
      name: "Renaming 400 Error",
      mocks: [defaultMock, userMock, renameErrorMock],
      props: { consultationId },
    },
    {
      name: "Renaming Throws Error",
      mocks: [defaultMock, userMock, renameThrowsMock],
      props: { consultationId },
    },
  ],
};
