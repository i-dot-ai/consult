import ErrorScreen from "./ErrorScreen.svelte";

const status = $state(404);

export default {
  name: "ErrorScreen",
  component: ErrorScreen,
  category: "Screens",
  props: [
    {
      name: "status",
      value: status,
      type: "select",
      options: [
        { value: 404, label: "404" },
        { value: 500, label: "500" },
      ],
    },
  ],
  stories: [
    {
      name: "Status 404",
      props: { status: 404 },
    },
    {
      name: "Status 500",
      props: { status: 500 },
    },
  ],
};
