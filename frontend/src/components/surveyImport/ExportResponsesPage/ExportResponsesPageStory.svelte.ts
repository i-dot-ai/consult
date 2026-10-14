import ExportResponsesPage from "./ExportResponsesPage.svelte";
import { CONSULTATION_ID, updateErrorMock, updateMock } from "./mocks";

const consultationId = $state(CONSULTATION_ID);
const dataSource = $state("citizen-space");

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
      mocks: [updateMock],
      props: { consultationId: CONSULTATION_ID, dataSource: null },
    },
    {
      name: "Qualtrics Saved",
      mocks: [updateMock],
      props: { consultationId: CONSULTATION_ID, dataSource: "qualtrics" },
    },
    {
      name: "Save Fails",
      mocks: [updateErrorMock],
      props: { consultationId: CONSULTATION_ID, dataSource: null },
    },
  ],
};
