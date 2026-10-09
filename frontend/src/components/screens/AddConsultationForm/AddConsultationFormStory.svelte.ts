import AddConsultationForm from "./AddConsultationForm.svelte";
import { consultationsMock, lookupMock } from "./mocks";

export default {
  name: "AddConsultationForm",
  component: AddConsultationForm,
  category: "Screens",
  mocks: [consultationsMock, lookupMock],
  props: [],
  stories: [
    {
      name: "No Duplicate",
      mocks: [
        consultationsMock,
        {
          ...lookupMock,
          body: {
            ...lookupMock.body,
            results: [],
          },
        },
      ],
    },
  ],
};
