import ThemeForm from "./ThemeForm.svelte";

const handleConfirm = (title: string, description: string) =>
  alert(`Saved: "${title}" — ${description}`);
const handleCancel = () => alert("Cancel event triggered");

export default {
  name: "ThemeForm",
  component: ThemeForm,
  category: "Finalising Themes",
  props: [
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
        initialTitle: "",
        initialDescription: "",
        handleConfirm,
        handleCancel,
      },
    },
    {
      name: "Edit Variant",
      props: {
        variant: "edit",
        initialTitle: "Data Privacy Concerns",
        initialDescription:
          "Responses discussing concerns about how personal data is collected, stored, or used.",
        handleConfirm,
        handleCancel,
      },
    },
  ],
};
