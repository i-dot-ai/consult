import FindThemesForm from "./FindThemesForm.svelte";
import { CONSULTATION_ID, findMock } from "./mocks";

const consultations = $state([
  {
    id: CONSULTATION_ID,
    title: "Folder 1",
    code: "folder-one",
  },
]);

export default {
  name: "FindThemesForm",
  component: FindThemesForm,
  category: "Screens / Support",
  mocks: [findMock],
  props: [{ name: "consultations", value: consultations, type: "json" }],
  stories: [
    {
      name: "Success",
      mocks: [findMock],
      props: { consultations },
    },
    {
      name: "Fetch Error",
      mocks: [{ ...findMock, throws: new Error("Error") }],
      props: { consultations },
    },
    {
      name: "4xx Error",
      mocks: [{ ...findMock, status: 400 }],
      props: { consultations },
    },
    {
      name: "5xx Error",
      mocks: [{ ...findMock, status: 500 }],
      props: { consultations },
    },
  ],
};
