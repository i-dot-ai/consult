import ManageConsultationsArchive from "./ManageConsultationsArchive.svelte";
import { CONSULTATIONS } from "./testData";

const consultations = $state(CONSULTATIONS);

export default {
  name: "ManageConsultationsArchive",
  component: ManageConsultationsArchive,
  category: "Screens / Support",
  props: [{ name: "consultations", value: consultations, type: "json" }],
  stories: [
    {
      name: "No Consultations",
      props: { consultations: [] },
    },
  ],
};
