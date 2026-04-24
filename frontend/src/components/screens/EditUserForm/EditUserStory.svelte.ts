import EditUser from "./EditUser.svelte";
import { getMock, patchMock } from "./mocks";

const userId = $state(["test-user"]);

export default {
  name: "EditUser",
  component: EditUser,
  category: "Screens / Support",
  mocks: [getMock, patchMock],
  props: [{ name: "userId", value: userId, type: "text" }],
  stories: [
    {
      name: "Success",
      mocks: [getMock, patchMock],
      props: { userId: "test-user" },
    },
    {
      name: "4xx Error Patch",
      mocks: [getMock, { ...patchMock, status: 400 }],
      props: { userId: "test-user" },
    },
    {
      name: "5xx Error Patch",
      mocks: [getMock, { ...patchMock, status: 500 }],
      props: { userId: "test-user" },
    },
    {
      name: "Fetch Error Patch",
      mocks: [getMock, { ...patchMock, throws: new Error("Fetch Failed") }],
      props: { userId: "test-user" },
    },
    {
      name: "4xx Error Get",
      mocks: [{ ...getMock, status: 400, body: undefined }, patchMock],
      props: { userId: "test-user" },
    },
    {
      name: "5xx Error Get",
      mocks: [{ ...getMock, status: 500, body: undefined }, patchMock],
      props: { userId: "test-user" },
    },
    {
      name: "Fetch Error Get",
      mocks: [{ ...getMock, throws: new Error("Fetch Failed") }, patchMock],
      props: { userId: "test-user" },
    },
  ],
};
