import ConsultationList from "./ConsultationList.svelte";

import { defaultMock, emptyMock, longMock, manyUsersMock } from "./mocks";

export default {
  name: "ConsultationList",
  component: ConsultationList,
  category: "Screens",
  mocks: [defaultMock],
  props: [],
  stories: [
    {
      name: "No Consultations",
      mocks: [emptyMock],
    },
    {
      name: "Many Consultations",
      mocks: [longMock],
    },
    {
      name: "Fetch Error",
      mocks: [{ ...defaultMock, throws: new Error("Fetch Error") }],
    },
    {
      name: "Many Users",
      mocks: [manyUsersMock],
    },
  ],
};
