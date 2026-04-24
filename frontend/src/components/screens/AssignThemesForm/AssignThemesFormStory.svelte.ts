import AssignThemesForm from "./AssignThemesForm.svelte";
import { CONSULTATION_ID, assignMock } from "./mocks";

const consultations = $state([
  {
    id: CONSULTATION_ID,
    title: "Folder 1",
    code: "folder-one",
  },
]);

export default {
  name: "AssignThemesForm",
  component: AssignThemesForm,
  category: "Screens / Support",
  mocks: [assignMock],
  props: [{ name: "consultations", value: consultations, type: "json" }],
  stories: [
    {
      name: "Success",
      mocks: [assignMock],
      props: { consultations },
    },
    {
      name: "Fetch Error",
      mocks: [{ ...assignMock, throws: new Error("Error") }],
      props: { consultations },
    },
    {
      name: "4xx Error",
      mocks: [{ ...assignMock, status: 400 }],
      props: { consultations },
    },
    {
      name: "5xx Error",
      mocks: [{ ...assignMock, status: 500 }],
      props: { consultations },
    },
  ],
};
