import { consultationErrorMock, consultationMock, userMock } from "./mocks";
import Overview from "./Overview.svelte";

const consultationId = $state("test-consultation");

export default {
  name: "Overview",
  component: Overview,
  category: "Screens / Survey Import",
  mocks: [userMock, consultationMock],
  props: [{ name: "consultationId", value: consultationId, type: "text" }],
  stories: [
    {
      name: "Fetch Error",
      mocks: [userMock, consultationErrorMock],
      props: { consultationId: consultationId },
    },
  ],
};
