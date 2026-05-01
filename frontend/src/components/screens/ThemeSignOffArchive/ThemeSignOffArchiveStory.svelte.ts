import { CONSULTATION_ID, consultationMock, consultationUpdateMock, questionsAllSignedOffMock, questionsMock } from "./mocks";
import ThemeSignOffArchive from "./ThemeSignOffArchive.svelte";

const consultationId = $state("test-consultation");

export default {
  name: "ThemeSignOffArchive",
  component: ThemeSignOffArchive,
  category: "Screens",
  mocks: [
    consultationMock,
    consultationUpdateMock,
    questionsMock,
  ],
  props: [
    { name: "consultationId", value: consultationId, type: "text" },
  ],
  stories: [
    {
      name: "Success Theme Sign Off Stage",
      mocks: [
        consultationMock,
        questionsMock,
      ],
      props: { consultationId: CONSULTATION_ID },
    },
    {
      name: "Success Theme Sign Off Stage All Signed Off",
      mocks: [
        consultationMock,
        consultationUpdateMock,
        questionsAllSignedOffMock,
      ],
      props: { consultationId: CONSULTATION_ID },
    },
    {
      name: "Success Theme Mapping Stage",
      mocks: [
        {
          ...consultationMock,
          body: {
            ...consultationMock.body,
            stage: "theme_mapping",
          }
        },
        questionsMock,
      ],
      props: { consultationId: CONSULTATION_ID },
    },
    {
      name: "Success Analysis Stage",
      mocks: [
        {
          ...consultationMock,
          body: {
            ...consultationMock.body,
            stage: "analysis",
          }
        },
        questionsMock,
      ],
      props: { consultationId: CONSULTATION_ID },
    },
    {
      name: "Questions 4xx Error",
      mocks: [
        consultationMock,
        {
          ...questionsMock,
          status: 400,
          body: undefined,
        },
      ],
      props: { consultationId: CONSULTATION_ID },
    },
    {
      name: "Questions 5xx Error",
      mocks: [
        consultationMock,
        {
          ...questionsMock,
          status: 500,
          body: undefined,
        },
      ],
      props: { consultationId: CONSULTATION_ID },
    },
    {
      name: "Questions Fetch Error",
      mocks: [
        consultationMock,
        {
          ...questionsMock,
          throws: new Error("Fetch error"),
        },
      ],
      props: { consultationId: CONSULTATION_ID },
    },
    {
      name: "Consultation 4xx Error",
      mocks: [
        {
          ...consultationMock,
          status: 400,
          body: undefined,
        },
        questionsMock,
      ],
      props: { consultationId: CONSULTATION_ID },
    },
    {
      name: "Consultation 5xx Error",
      mocks: [
        {
          ...consultationMock,
          status: 500,
          body: undefined,
        },
        questionsMock,
      ],
      props: { consultationId: CONSULTATION_ID },
    },
    {
      name: "Consultation Fetch Error",
      mocks: [
        {
          ...consultationMock,
          throws: new Error("Fetch error"),
        },
        questionsMock,
      ],
      props: { consultationId: CONSULTATION_ID },
    },
  ],
};
