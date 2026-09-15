import Error from "../svg/material/Error.svelte";
import Help from "../svg/material/Help.svelte";
import Alert from "./Alert.svelte";
import { childrenDefault, childrenLong } from "./testData";

let children = $state(childrenDefault);
let Icon = $state(Help);

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
  ],
  stories: [
    {
      name: "Long Content",
      props: {
        children: childrenLong,
      },
    },
    {
      name: "Error Variant",
      props: {
        children: childrenDefault,
        Icon: Error,
      },
    },
  ],
};
