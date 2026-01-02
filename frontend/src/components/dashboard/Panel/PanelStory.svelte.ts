import { createRawSnippet } from "svelte";

import Panel from "./Panel.svelte";

const variant = $state("default");
const childrenHtml = $state("<p>Child Element</p>");
const border = $state(true);
const bg = $state(false);
const level = $state(1);

const childrenComponent = $derived.by(() => {
  try {
    return createRawSnippet(() => ({
      render: () => childrenHtml,
    }));
  } catch {
    return createRawSnippet(() => ({
      render: () => "<p>Child Element</p>",
    }));
  }
});

export default {
  name: "Panel",
  component: Panel,
  props: [
    {
      name: "variant",
      value: variant,
      type: "select",
      options: [
        { value: "default", label: "Default" },
        { value: "primary", label: "Primary" },
        { value: "approve", label: "Approve" },
      ],
    },
    {
      name: "border",
      value: border,
      type: "bool",
    },
    {
      name: "bg",
      value: bg,
      type: "bool",
    },
    {
      name: "level",
      value: level,
      type: "number",
    },
    {
      name: "children",
      value: childrenComponent,
      type: "html",
      rawHtml: childrenHtml,
    },
  ],
  stories: [],
};
