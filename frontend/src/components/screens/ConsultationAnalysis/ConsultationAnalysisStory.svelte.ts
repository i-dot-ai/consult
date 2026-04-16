import ConsultationAnalysis from "./ConsultationAnalysis.svelte";
import {
  CONSULTATION_ID,
  consultationMock,
  demoOptionsMock,
  questionsMock,
} from "./mocks";

const consultationId = $state("test-consultation");

export default {
  name: "ConsultationAnalysis",
  component: ConsultationAnalysis,
  category: "Screens",
  mocks: [consultationMock, questionsMock, demoOptionsMock],
  props: [{ name: "consultationId", value: consultationId, type: "text" }],
  stories: [
    {
      name: "No Questions",
      mocks: [
        consultationMock,
        {
          ...questionsMock,
          body: {
            count: 0,
            next: null,
            previous: null,
            results: [],
          },
        },
        demoOptionsMock,
      ],
      props: {
        consultationId: CONSULTATION_ID,
      },
    },

    // Questions Errors
    {
      name: "Questions Error 4xx",
      mocks: [
        consultationMock,
        {
          ...questionsMock,
          status: 400,
          body: undefined,
        },
        demoOptionsMock,
      ],
      props: {
        consultationId: CONSULTATION_ID,
      },
    },
    {
      name: "Questions Error 5xx",
      mocks: [
        consultationMock,
        {
          ...questionsMock,
          status: 500,
          body: undefined,
        },
        demoOptionsMock,
      ],
      props: {
        consultationId: CONSULTATION_ID,
      },
    },
    {
      name: "Questions Fetch Error",
      mocks: [
        consultationMock,
        {
          ...questionsMock,
          throws: new Error("Fetch Error"),
        },
        demoOptionsMock,
      ],
      props: {
        consultationId: CONSULTATION_ID,
      },
    },

    // Consultation Errors
    {
      name: "Consultation 4xx Error",
      mocks: [
        {
          ...consultationMock,
          status: 400,
          body: undefined,
        },
        questionsMock,
        demoOptionsMock,
      ],
      props: {
        consultationId: CONSULTATION_ID,
      },
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
        demoOptionsMock,
      ],
      props: {
        consultationId: CONSULTATION_ID,
      },
    },
    {
      name: "Consultation Fetch Error",
      mocks: [
        {
          ...consultationMock,
          throws: new Error("Fetch Error"),
        },
        questionsMock,
        demoOptionsMock,
      ],
      props: {
        consultationId: CONSULTATION_ID,
      },
    },

    // Demo Options Errors
    {
      name: "Demo Optons 4xx Error",
      mocks: [
        questionsMock,
        consultationMock,
        {
          ...demoOptionsMock,
          status: 400,
          body: undefined,
        },
      ],
      props: {
        consultationId: CONSULTATION_ID,
      },
    },
    {
      name: "Demo Optons 5xx Error",
      mocks: [
        questionsMock,
        consultationMock,
        {
          ...demoOptionsMock,
          status: 500,
          body: undefined,
        },
      ],
      props: {
        consultationId: CONSULTATION_ID,
      },
    },
    {
      name: "Demo Optons Fetch Error",
      mocks: [
        questionsMock,
        consultationMock,
        {
          ...demoOptionsMock,
          throws: new Error("Fetch Error"),
        },
      ],
      props: {
        consultationId: CONSULTATION_ID,
      },
    },
  ],
};
