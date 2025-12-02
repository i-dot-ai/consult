import ThemeForm from "./ThemeForm.svelte";

const variant = $state("add");
const handleConfirm = () => alert("Confirm event triggered");
const handleCancel = () => alert("Cancel event triggered");

export default {
  name: "ThemeForm",
  component: ThemeForm,
  category: "Theme Sign Off",
  props: [
    {
      name: "variant",
      value: variant,
      type: "select",
      options: [
        { value: "add", label: "Add" },
        { value: "edit", label: "Edit" },
      ],
    },
    {
      name: "handleConfirm",
      value: handleConfirm,
      type: "func",
      schema: "(title: string, description: string) => void",
    },
    {
      name: "handleCancel",
      value: handleCancel,
      type: "func",
      schema: "() => void",
    },
  ],
  stories: [
    {
      name: "Add Variant",
      props: {
        variant: "add",
        handleConfirm: handleConfirm,
        handleCancel: handleCancel,
      },
    },
    {
      name: "Edit Variant",
      props: {
        variant: "edit",
        handleConfirm: handleConfirm,
        handleCancel: handleCancel,
      },
    },
  ],
};
