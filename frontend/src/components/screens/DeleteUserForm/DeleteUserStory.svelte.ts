import DeleteUserForm from "./DeleteUserForm.svelte";
import { USER } from "./mocks";
import { deleteMock } from "./mocks";

const user = $state(USER);

export default {
  name: "DeleteUserForm",
  component: DeleteUserForm,
  category: "Screens / Support",
  mocks: [deleteMock],
  props: [{ name: "user", value: user, type: "json" }],
  stories: [
    {
      name: "Success",
      mocks: [deleteMock],
      props: { user: user },
    },
    {
      name: "Fetch Error",
      mocks: [{ ...deleteMock, throws: new Error("Error") }],
      props: { user: user },
    },
    {
      name: "4xx Error",
      mocks: [{ ...deleteMock, status: 400 }],
      props: { user: user },
    },
    {
      name: "5xx Error",
      mocks: [{ ...deleteMock, status: 500 }],
      props: { user: user },
    },
  ],
};
