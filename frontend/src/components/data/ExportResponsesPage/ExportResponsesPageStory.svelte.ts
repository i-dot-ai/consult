import ExportResponsesPage from "./ExportResponsesPage.svelte";
import { CONSULTATION_ID, updateErrorMock, updateMock } from "./mocks";

const consultationId = $state(CONSULTATION_ID);
const dataSource = $state("qualtrics");

export default {
  name: "ExportResponsesPage",
  component: ExportResponsesPage,
  category: "Data",
  mocks: [updateMock],
  props: [
    { name: "consultationId", value: consultationId, type: "text" },
    {
      name: "dataSource",
      value: dataSource,
      type: "select",
      options: [
        { label: "Qualtrics", value: "qualtrics" },
        { label: "Citizen Space", value: "citizen-space" },
      ],
    },
  ],
  stories: [
    {
      name: "Nothing Saved Yet",
      props: { consultationId: CONSULTATION_ID, dataSource: null },
    },
    {
      name: "Citizen Space Saved",
      props: { consultationId: CONSULTATION_ID, dataSource: "citizen-space" },
    },
    {
      name: "Save Fails",
      mocks: [updateErrorMock],
      props: { consultationId: CONSULTATION_ID, dataSource: null },
    },
  ],
};
