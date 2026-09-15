import CheckCircle from "../svg/material/CheckCircle.svelte";
import Error from "../svg/material/Error.svelte";
import Help from "../svg/material/Help.svelte";
import Alert from "./Alert.svelte";
import { childrenDefault, childrenLong, defaultVariant } from "./testData";

const children = $state(childrenDefault);
const Icon = $state(Help);
const variant = $state(defaultVariant);

export default {
  name: "Alert",
  component: Alert,
  props: [
    {
      name: "Icon",
      value: Icon,
      type: "select",
      options: [
        { value: Error, label: "Error" },
        { value: Help, label: "Help" },
      ],
    },
    {
      name: "children",
      value: children,
      type: "select",
      options: [
        { value: childrenDefault, label: "Child with Default Content" },
        { value: childrenLong, label: "Child with Long Content" },
      ],
    },
    {
      name: "variant",
      value: variant,
      type: "select",
      options: [
        { value: "info", label: "Info" },
        { value: "warning", label: "Warning" },
        { value: "error", label: "Error" },
        { value: "success", label: "Success" },
      ],
    },
  ],
  stories: [
    {
      name: "Long Content",
      props: {
        children: childrenLong,
        Icon: Help,
      },
    },
    {
      name: "Error Variant",
      props: {
        children: childrenDefault,
        Icon: Error,
        variant: "error",
      },
    },
    {
      name: "Success Variant",
      props: {
        children: childrenDefault,
        Icon: CheckCircle,
        variant: "success",
      },
    },
  ],
};
