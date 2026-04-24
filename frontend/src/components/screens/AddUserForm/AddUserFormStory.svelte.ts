import AddUserForm from "./AddUserForm.svelte";
import { defaultMock } from "./mocks";

export default {
  name: "AddUserForm",
  component: AddUserForm,
  category: "Screens / Support",
  mocks: [defaultMock],
  props: [],
  stories: [
    {
      name: "Success",
      mocks: [defaultMock],
    },
    {
      name: "4xx Error",
      mocks: [
        {
          ...defaultMock,
          status: 400,
        },
      ],
    },
    {
      name: "5xx Error",
      mocks: [
        {
          ...defaultMock,
          status: 500,
        },
      ],
    },
    {
      name: "Fetch Error",
      mocks: [
        {
          ...defaultMock,
          throws: new Error("Fetch Failed"),
        },
      ],
    },
  ],
};
