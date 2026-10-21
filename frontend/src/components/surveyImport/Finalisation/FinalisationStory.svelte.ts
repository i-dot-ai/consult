import Finalisation from "./Finalisation.svelte";
import { CONSULTATION_ID } from "./mocks";

const consultationId = $state(CONSULTATION_ID);

export default {
  name: "Finalisation",
  component: Finalisation,
  category: "Data",
  props: [{ name: "consultationId", value: consultationId, type: "text" }],
  stories: [
    {
      name: "Default",
      props: { consultationId: CONSULTATION_ID },
    },
  ],
};
