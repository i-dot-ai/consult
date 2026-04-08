import ConsultationList from "./ConsultationList.svelte";

import { defaultMock, emptyMock, longMock } from "./mocks";

export default {
  name: "ConsultationList",
  component: ConsultationList,
  category: "Screens",
  mock: defaultMock,
  props: [],
  stories: [
    {
      name: "No Consultations",
      mock: emptyMock,
    },
    {
      name: "Many Consultations",
      mock: longMock,
    }
  ],
};
