import InsetText from "./InsetText.svelte";

export default {
  name: "InsetText",
  component: InsetText,
  props: [
    {
      name: "variant",
      type: "select",
      value: "default",
      schema: "default|info|warning|success|error",
    },
    {
      name: "className",
      type: "text",
      value: "",
    },
  ],
  stories: [
    {
      name: "Default",
      props: {
        variant: "default",
      },
    },
    {
      name: "Info",
      props: {
        variant: "info",
      },
    },
    {
      name: "Warning",
      props: {
        variant: "warning",
      },
    },
    {
      name: "Success",
      props: {
        variant: "success",
      },
    },
    {
      name: "Error",
      props: {
        variant: "error",
      },
    },
  ],
};
