import ChecksPage from "./ChecksPage.svelte";
import { CONSULTATION_ID } from "./mocks";

const consultationId = CONSULTATION_ID;

export default {
  name: "ChecksPage",
  component: ChecksPage,
  category: "Screens / Survey Import",
  props: [{ name: "consultationId", value: consultationId, type: "text" }],
  stories: [
    {
      name: "Qualtrics",
      props: { consultationId: CONSULTATION_ID, dataSource: "qualtrics" },
    },
    {
      name: "Citizen Space",
      props: { consultationId: CONSULTATION_ID, dataSource: "citizen-space" },
    },
  ],
};
